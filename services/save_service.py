from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging
from datetime import date
from schemas.student_schema import SaveStudentRequest, SaveStudentResponse
from schemas.education_schema import SaveSchoolRequest, SaveEducationRequest
from schemas.workexp_schema import SaveWorkExpRequest, SaveWorkExpResponse
from schemas.project_schema import SaveProjectRequest, SaveProjectResponse
from schemas.address_schema import SaveAddressRequest, SaveAddressResponse
from utils.date_utils import safe_date

logger = logging.getLogger(__name__)


async def save_student(db: AsyncSession, data: SaveStudentRequest) -> SaveStudentResponse:
    """
    Saves a student record to tbl_cp_student.
    Returns existing student_id if email already exists.
    
    Parameters:
        db: Database session
        data: SaveStudentRequest with student details
        
    Returns:
        SaveStudentResponse with student_id and already_exists flag
    """
    logger.debug(f"Checking if student exists: {data.email}")
    
    # Check if student with same email exists
    result = await db.execute(
        text("SELECT student_id FROM tbl_cp_student WHERE email = :email"),
        {"email": data.email}
    )
    existing = result.fetchone()
    
    if existing:
        logger.debug(f"Student already exists: {existing[0]}")
        return SaveStudentResponse(student_id=existing[0], already_exists=True)
    
    # Get next student_id
    result = await db.execute(text("SELECT COALESCE(MAX(student_id), 0) + 1 FROM tbl_cp_student"))
    next_id = result.scalar()
    
    # Apply defaults
    date_of_birth = safe_date(data.date_of_birth, date(1900, 1, 1))
    
    # Insert new student
    await db.execute(
        text("""INSERT INTO tbl_cp_student 
                (student_id, salutation_id, first_name, middle_name, last_name, email, alt_email,
                 contact_number, alt_contact_number, linkedin_url, github_url, portfolio_url,
                 date_of_birth, current_city, gender, user_type, is_active, status, profile_photo_url)
                VALUES (:student_id, :salutation_id, :first_name, :middle_name, :last_name, :email, :alt_email,
                        :contact_number, :alt_contact_number, :linkedin_url, :github_url, :portfolio_url,
                        :date_of_birth, :current_city, :gender, :user_type, :is_active, :status, :profile_photo_url)"""),
        {
            "student_id": next_id,
            "salutation_id": data.salutation_id,
            "first_name": data.first_name,
            "middle_name": data.middle_name or '',
            "last_name": data.last_name or '',
            "email": data.email,
            "alt_email": data.alt_email or '',
            "contact_number": data.contact_number,
            "alt_contact_number": data.alt_contact_number or '0000000000',
            "linkedin_url": data.linkedin_url or '',
            "github_url": data.github_url or '',
            "portfolio_url": data.portfolio_url or '',
            "date_of_birth": date_of_birth.strftime('%Y-%m-%d'),
            "current_city": data.current_city or 'Not Specified',
            "gender": data.gender or 'Not Specified',
            "user_type": 'Student',
            "is_active": True,
            "status": 'Active',
            "profile_photo_url": 'default_profile.png'
        }
    )
    await db.commit()
    logger.debug(f"Student saved: {next_id}")
    
    return SaveStudentResponse(student_id=next_id, already_exists=False)


async def save_school(db: AsyncSession, data: SaveSchoolRequest):
    """
    Saves a school record to tbl_cp_student_school.
    
    Parameters:
        db: Database session
        data: SaveSchoolRequest with school details
        
    Returns:
        dict with school_id
    """
    logger.debug(f"Saving school for student: {data.student_id}")
    
    # Get next school_id
    result = await db.execute(text("SELECT COALESCE(MAX(school_id), 0) + 1 FROM tbl_cp_student_school"))
    next_id = result.scalar()
    
    # Insert new school
    await db.execute(
        text("""INSERT INTO tbl_cp_student_school 
                (school_id, student_id, standard, board, school_name, percentage, passing_year)
                VALUES (:school_id, :student_id, :standard, :board, :school_name, :percentage, :passing_year)"""),
        {
            "school_id": next_id,
            "student_id": data.student_id,
            "standard": data.standard,
            "board": data.board or 'Not Specified',
            "school_name": data.school_name or 'Not Specified',
            "percentage": data.percentage or 0.00,
            "passing_year": data.passing_year or 0
        }
    )
    await db.commit()
    logger.debug(f"School saved: {next_id}")
    
    return {"school_id": next_id}


async def save_education(db: AsyncSession, data: SaveEducationRequest):
    """
    Saves a college education record to tbl_cp_student_education.
    
    Parameters:
        db: Database session
        data: SaveEducationRequest with education details
        
    Returns:
        dict with edu_id
    """
    logger.debug(f"Saving education for student: {data.student_id}")
    
    # Get next edu_id
    result = await db.execute(text("SELECT COALESCE(MAX(edu_id), 0) + 1 FROM tbl_cp_student_education"))
    next_id = result.scalar()
    
    # Insert new education
    await db.execute(
        text("""INSERT INTO tbl_cp_student_education 
                (edu_id, student_id, college_id, course_id, start_year, end_year, cgpa, percentage)
                VALUES (:edu_id, :student_id, :college_id, :course_id, :start_year, :end_year, :cgpa, :percentage)"""),
        {
            "edu_id": next_id,
            "student_id": data.student_id,
            "college_id": data.college_id,
            "course_id": data.course_id,
            "start_year": data.start_year or 0,
            "end_year": data.end_year or 0,
            "cgpa": data.cgpa or 0.00,
            "percentage": data.percentage or 0.00
        }
    )
    await db.commit()
    logger.debug(f"Education saved: {next_id}")
    
    return {"edu_id": next_id}


async def save_workexp(db: AsyncSession, data: SaveWorkExpRequest) -> SaveWorkExpResponse:
    """
    Saves a work experience record to tbl_cp_student_workexp.
    
    Parameters:
        db: Database session
        data: SaveWorkExpRequest with work experience details
        
    Returns:
        SaveWorkExpResponse with workexp_id
    """
    logger.debug(f"Saving work experience for student: {data.student_id}")
    
    # Get next workexp_id
    result = await db.execute(text("SELECT COALESCE(MAX(workexp_id), 0) + 1 FROM tbl_cp_student_workexp"))
    next_id = result.scalar()
    
    # Handle dates
    start_date = safe_date(data.start_date, date(1900, 1, 1))
    
    # If is_current is True, set end_date to 1900-01-01
    if data.is_current:
        end_date = date(1900, 1, 1)
    else:
        end_date = safe_date(data.end_date, date(1900, 1, 1))
    
    # Insert new work experience
    await db.execute(
        text("""INSERT INTO tbl_cp_student_workexp 
                (workexp_id, student_id, company_name, company_location, designation, employment_type, start_date, end_date, is_current)
                VALUES (:workexp_id, :student_id, :company_name, :company_location, :designation, :employment_type, :start_date, :end_date, :is_current)"""),
        {
            "workexp_id": next_id,
            "student_id": data.student_id,
            "company_name": data.company_name,
            "company_location": data.company_location or 'Not Specified',
            "designation": data.designation or 'Not Specified',
            "employment_type": data.employment_type or 'Full-Time',
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "is_current": data.is_current
        }
    )
    await db.commit()
    logger.debug(f"Work experience saved: {next_id}")
    
    return SaveWorkExpResponse(workexp_id=next_id)


async def save_project(db: AsyncSession, data: SaveProjectRequest) -> SaveProjectResponse:
    """
    Saves a project record to tbl_cp_studentprojects.
    
    Parameters:
        db: Database session
        data: SaveProjectRequest with project details
        
    Returns:
        SaveProjectResponse with project_id
    """
    logger.debug(f"Saving project for student: {data.student_id}")
    
    # Get next project_id
    result = await db.execute(text("SELECT COALESCE(MAX(project_id), 0) + 1 FROM tbl_cp_studentprojects"))
    next_id = result.scalar()
    
    # Handle dates
    start_date = safe_date(data.project_start_date, date(1900, 1, 1))
    end_date = safe_date(data.project_end_date, date(1900, 1, 1))
    
    # Insert new project
    await db.execute(
        text("""INSERT INTO tbl_cp_studentprojects 
                (project_id, student_id, workexp_id, project_title, project_description, achievements, project_start_date, project_end_date)
                VALUES (:project_id, :student_id, :workexp_id, :project_title, :project_description, :achievements, :project_start_date, :project_end_date)"""),
        {
            "project_id": next_id,
            "student_id": data.student_id,
            "workexp_id": data.workexp_id,
            "project_title": data.project_title,
            "project_description": data.project_description,
            "achievements": data.achievements,
            "project_start_date": start_date.strftime('%Y-%m-%d'),
            "project_end_date": end_date.strftime('%Y-%m-%d')
        }
    )
    await db.commit()
    logger.debug(f"Project saved: {next_id}")
    
    return SaveProjectResponse(project_id=next_id)


async def save_project_skill(db: AsyncSession, project_id: int, skill_id: int):
    """
    Saves a project-skill many-to-many relationship to tbl_cp_m2m_studentproject_skill.
    Does not error if relationship already exists.
    
    Parameters:
        db: Database session
        project_id: Project ID
        skill_id: Skill ID
        
    Returns:
        dict with already_exists flag
    """
    logger.debug(f"Saving project skill: project_id={project_id}, skill_id={skill_id}")
    
    # Check if already exists
    result = await db.execute(
        text("SELECT row_id FROM tbl_cp_m2m_studentproject_skill WHERE project_id = :project_id AND skill_id = :skill_id"),
        {"project_id": project_id, "skill_id": skill_id}
    )
    
    if result.fetchone():
        logger.debug(f"Project skill already exists")
        return {"already_exists": True}
    
    # Insert new relationship
    await db.execute(
        text("""INSERT INTO tbl_cp_m2m_studentproject_skill (project_id, skill_id)
                VALUES (:project_id, :skill_id)"""),
        {"project_id": project_id, "skill_id": skill_id}
    )
    await db.commit()
    logger.debug(f"Project skill saved")
    
    return {"already_exists": False}


async def save_student_skill(db: AsyncSession, student_id: int, skill_id: int):
    """
    Saves a student-skill many-to-many relationship to tbl_cp_m2m_std_skill.
    Does not error if relationship already exists.
    
    Parameters:
        db: Database session
        student_id: Student ID
        skill_id: Skill ID
        
    Returns:
        dict with already_exists flag
    """
    logger.debug(f"Saving student skill: student_id={student_id}, skill_id={skill_id}")
    
    # Check if already exists
    result = await db.execute(
        text("SELECT row_id FROM tbl_cp_m2m_std_skill WHERE student_id = :student_id AND skill_id = :skill_id"),
        {"student_id": student_id, "skill_id": skill_id}
    )
    
    if result.fetchone():
        logger.debug(f"Student skill already exists")
        return {"already_exists": True}
    
    # Insert new relationship
    await db.execute(
        text("""INSERT INTO tbl_cp_m2m_std_skill (student_id, skill_id)
                VALUES (:student_id, :skill_id)"""),
        {"student_id": student_id, "skill_id": skill_id}
    )
    await db.commit()
    logger.debug(f"Student skill saved")
    
    return {"already_exists": False}


async def save_student_language(db: AsyncSession, student_id: int, language_id: int):
    """
    Saves a student-language many-to-many relationship to tbl_cp_m2m_std_lng.
    
    Parameters:
        db: Database session
        student_id: Student ID
        language_id: Language ID
        
    Returns:
        dict with already_exists flag
    """
    logger.debug(f"Saving student language: student_id={student_id}, language_id={language_id}")
    
    # Check if already exists
    result = await db.execute(
        text("SELECT row_id FROM tbl_cp_m2m_std_lng WHERE student_id = :student_id AND language_id = :language_id"),
        {"student_id": student_id, "language_id": language_id}
    )
    
    if result.fetchone():
        logger.debug(f"Student language already exists")
        return {"already_exists": True}
    
    # Insert new relationship
    await db.execute(
        text("""INSERT INTO tbl_cp_m2m_std_lng (student_id, language_id)
                VALUES (:student_id, :language_id)"""),
        {"student_id": student_id, "language_id": language_id}
    )
    await db.commit()
    logger.debug(f"Student language saved")
    
    return {"already_exists": False}


async def save_student_interest(db: AsyncSession, student_id: int, interest_id: int):
    """
    Saves a student-interest many-to-many relationship to tbl_cp_m2m_std_interest.
    
    Parameters:
        db: Database session
        student_id: Student ID
        interest_id: Interest ID
        
    Returns:
        dict with already_exists flag
    """
    logger.debug(f"Saving student interest: student_id={student_id}, interest_id={interest_id}")
    
    # Check if already exists
    result = await db.execute(
        text("SELECT row_id FROM tbl_cp_m2m_std_interest WHERE student_id = :student_id AND interest_id = :interest_id"),
        {"student_id": student_id, "interest_id": interest_id}
    )
    
    if result.fetchone():
        logger.debug(f"Student interest already exists")
        return {"already_exists": True}
    
    # Insert new relationship
    await db.execute(
        text("""INSERT INTO tbl_cp_m2m_std_interest (student_id, interest_id)
                VALUES (:student_id, :interest_id)"""),
        {"student_id": student_id, "interest_id": interest_id}
    )
    await db.commit()
    logger.debug(f"Student interest saved")
    
    return {"already_exists": False}


async def save_student_certification(db: AsyncSession, data: dict):
    """
    Saves a student-certification many-to-many relationship to tbl_cp_m2m_student_certification.
    
    Parameters:
        db: Database session
        data: Dict with student_id, certification_id, and optional dates/urls
        
    Returns:
        dict with already_exists flag
    """
    logger.debug(f"Saving student certification: student_id={data.get('student_id')}, cert_id={data.get('certification_id')}")
    
    # Check if already exists
    result = await db.execute(
        text("SELECT row_id FROM tbl_cp_m2m_student_certification WHERE student_id = :student_id AND certification_id = :certification_id"),
        {"student_id": data["student_id"], "certification_id": data["certification_id"]}
    )
    
    if result.fetchone():
        logger.debug(f"Student certification already exists")
        return {"already_exists": True}
    
    # Handle dates
    issue_date = safe_date(data.get("issue_date"), date(1900, 1, 1))
    expiry_date = safe_date(data.get("expiry_date"), date(9999, 12, 31))
    
    # Insert new relationship
    await db.execute(
        text("""INSERT INTO tbl_cp_m2m_student_certification 
                (student_id, certification_id, issue_date, expiry_date, certificate_url, credential_id, is_verified)
                VALUES (:student_id, :certification_id, :issue_date, :expiry_date, :certificate_url, :credential_id, :is_verified)"""),
        {
            "student_id": data["student_id"],
            "certification_id": data["certification_id"],
            "issue_date": issue_date.strftime('%Y-%m-%d'),
            "expiry_date": expiry_date.strftime('%Y-%m-%d'),
            "certificate_url": data.get("certificate_url") or '',
            "credential_id": data.get("credential_id") or '',
            "is_verified": False
        }
    )
    await db.commit()
    logger.debug(f"Student certification saved")
    
    return {"already_exists": False}


async def save_address(db: AsyncSession, data: SaveAddressRequest) -> SaveAddressResponse:
    """
    Saves an address record to tbl_cp_student_address.
    
    Parameters:
        db: Database session
        data: SaveAddressRequest with address details
        
    Returns:
        SaveAddressResponse with address_id
    """
    logger.debug(f"Saving address for student: {data.student_id}")
    
    # Get next address_id
    result = await db.execute(text("SELECT COALESCE(MAX(address_id), 0) + 1 FROM tbl_cp_student_address"))
    next_id = result.scalar()
    
    # Insert new address
    await db.execute(
        text("""INSERT INTO tbl_cp_student_address 
                (address_id, student_id, address_line_1, address_line_2, care_of, landmark, pincode_id, 
                 latitude, longitude, address_type, address_expiry)
                VALUES (:address_id, :student_id, :address_line_1, :address_line_2, :care_of, :landmark, :pincode_id,
                        :latitude, :longitude, :address_type, :address_expiry)"""),
        {
            "address_id": next_id,
            "student_id": data.student_id,
            "address_line_1": data.address_line_1,
            "address_line_2": data.address_line_2 or '',
            "care_of": data.care_of or '',
            "landmark": data.landmark or 'No Landmark',
            "pincode_id": data.pincode_id,
            "latitude": '0.0',
            "longitude": '0.0',
            "address_type": data.address_type or 'current',
            "address_expiry": '9999-12-31'
        }
    )
    await db.commit()
    logger.debug(f"Address saved: {next_id}")
    
    return SaveAddressResponse(address_id=next_id)
