from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging
from schemas.lookup_schema import (
    LookupSkillResponse, LookupLanguageResponse, LookupInterestResponse,
    LookupCertificationResponse, LookupCollegeResponse, LookupCourseResponse,
    LookupSalutationResponse, LookupPincodeResponse
)

logger = logging.getLogger(__name__)

COURSE_CODE_MAP = {
    "bachelor of technology": "BTECH",
    "master of technology": "MTECH",
    "bachelor of engineering": "BE",
    "master of engineering": "ME",
    "bachelor of computer applications": "BCA",
    "master of computer applications": "MCA",
    "bachelor of business administration": "BBA",
    "master of business administration": "MBA",
    "bachelor of science": "BSC",
    "master of science": "MSC",
    "bachelor of commerce": "BCOM",
    "master of commerce": "MCOM",
    "bachelor of arts": "BA",
    "master of arts": "MA",
    "bachelor of computer science": "BCS",
    "doctor of philosophy": "PHD",
    "diploma": "DIP",
    "post graduate diploma": "PGD",
}


async def find_or_create_skill(db: AsyncSession, name: str, complexity: str = "Intermediate") -> LookupSkillResponse:
    """
    Finds or creates a skill in tbl_cp_mskills.
    
    Parameters:
        db: Database session
        name: Skill name
        complexity: Skill complexity level
        
    Returns:
        LookupSkillResponse with skill_id and is_new flag
    """
    logger.debug(f"Looking up skill: {name}")
    
    # Query for existing skill (case-insensitive)
    result = await db.execute(
        text("SELECT skill_id, name, complexity FROM tbl_cp_mskills WHERE LOWER(name) = LOWER(:name)"),
        {"name": name}
    )
    existing = result.fetchone()
    
    if existing:
        logger.debug(f"Skill found: {existing[0]}")
        return LookupSkillResponse(skill_id=existing[0], name=existing[1], complexity=existing[2], is_new=False)
    
    # Get next skill_id
    result = await db.execute(text("SELECT COALESCE(MAX(skill_id), 0) + 1 FROM tbl_cp_mskills"))
    next_id = result.scalar()
    
    # Get language_id for "General"
    result = await db.execute(text("SELECT language_id FROM tbl_cp_mlanguages WHERE LOWER(language_name) = 'general'"))
    lang_result = result.fetchone()
    language_id = lang_result[0] if lang_result else 1
    
    # Insert new skill
    try:
        await db.execute(
            text("""INSERT INTO tbl_cp_mskills 
                    (skill_id, name, complexity, language_id, description, version, status)
                    VALUES (:id, :name, :complexity, :language_id, :description, :version, :status)"""),
            {
                "id": next_id,
                "name": name,
                "complexity": complexity,
                "language_id": language_id,
                "description": "No description",
                "version": "N/A",
                "status": "Active"
            }
        )
        await db.commit()
        logger.debug(f"Skill created: {next_id}")
        return LookupSkillResponse(skill_id=next_id, name=name, complexity=complexity, is_new=True)
    except Exception as e:
        logger.error(f"Error creating skill: {e}")
        # On duplicate, try to fetch existing
        result = await db.execute(
            text("SELECT skill_id, name, complexity FROM tbl_cp_mskills WHERE LOWER(name) = LOWER(:name)"),
            {"name": name}
        )
        existing = result.fetchone()
        if existing:
            return LookupSkillResponse(skill_id=existing[0], name=existing[1], complexity=existing[2], is_new=False)
        raise


async def find_or_create_language(db: AsyncSession, language_name: str) -> LookupLanguageResponse:
    """
    Finds or creates a language in tbl_cp_mlanguages.
    
    Parameters:
        db: Database session
        language_name: Language name
        
    Returns:
        LookupLanguageResponse with language_id and language_code
    """
    logger.debug(f"Looking up language: {language_name}")
    
    # Query for existing language (case-insensitive)
    result = await db.execute(
        text("SELECT language_id, language_code FROM tbl_cp_mlanguages WHERE LOWER(language_name) = LOWER(:name)"),
        {"name": language_name}
    )
    existing = result.fetchone()
    
    if existing:
        logger.debug(f"Language found: {existing[0]}")
        return LookupLanguageResponse(language_id=existing[0], language_name=language_name, 
                                     language_code=existing[1], is_new=False)
    
    # Get next language_id
    result = await db.execute(text("SELECT COALESCE(MAX(language_id), 0) + 1 FROM tbl_cp_mlanguages"))
    next_id = result.scalar()
    
    # Generate language_code
    code = language_name[:3].upper()
    
    # Check if code already exists, append suffix if needed
    suffix = 2
    original_code = code
    while True:
        result = await db.execute(
            text("SELECT language_id FROM tbl_cp_mlanguages WHERE language_code = :code"),
            {"code": code}
        )
        if not result.fetchone():
            break
        code = f"{original_code}{suffix}"
        suffix += 1
    
    # Insert new language
    try:
        await db.execute(
            text("""INSERT INTO tbl_cp_mlanguages 
                    (language_id, language_code, language_name)
                    VALUES (:id, :code, :name)"""),
            {"id": next_id, "code": code, "name": language_name}
        )
        await db.commit()
        logger.debug(f"Language created: {next_id}")
        return LookupLanguageResponse(language_id=next_id, language_name=language_name, 
                                     language_code=code, is_new=True)
    except Exception as e:
        logger.error(f"Error creating language: {e}")
        result = await db.execute(
            text("SELECT language_id, language_code FROM tbl_cp_mlanguages WHERE LOWER(language_name) = LOWER(:name)"),
            {"name": language_name}
        )
        existing = result.fetchone()
        if existing:
            return LookupLanguageResponse(language_id=existing[0], language_name=language_name, 
                                         language_code=existing[1], is_new=False)
        raise


async def find_or_create_interest(db: AsyncSession, name: str) -> LookupInterestResponse:
    """
    Finds or creates an interest in tbl_cp_minterests.
    
    Parameters:
        db: Database session
        name: Interest name
        
    Returns:
        LookupInterestResponse with interest_id
    """
    logger.debug(f"Looking up interest: {name}")
    
    # Query for existing interest (case-insensitive)
    result = await db.execute(
        text("SELECT interest_id FROM tbl_cp_minterests WHERE LOWER(name) = LOWER(:name)"),
        {"name": name}
    )
    existing = result.fetchone()
    
    if existing:
        logger.debug(f"Interest found: {existing[0]}")
        return LookupInterestResponse(interest_id=existing[0], name=name, is_new=False)
    
    # Get next interest_id
    result = await db.execute(text("SELECT COALESCE(MAX(interest_id), 0) + 1 FROM tbl_cp_minterests"))
    next_id = result.scalar()
    
    # Insert new interest
    try:
        await db.execute(
            text("INSERT INTO tbl_cp_minterests (interest_id, name) VALUES (:id, :name)"),
            {"id": next_id, "name": name}
        )
        await db.commit()
        logger.debug(f"Interest created: {next_id}")
        return LookupInterestResponse(interest_id=next_id, name=name, is_new=True)
    except Exception as e:
        logger.error(f"Error creating interest: {e}")
        result = await db.execute(
            text("SELECT interest_id FROM tbl_cp_minterests WHERE LOWER(name) = LOWER(:name)"),
            {"name": name}
        )
        existing = result.fetchone()
        if existing:
            return LookupInterestResponse(interest_id=existing[0], name=name, is_new=False)
        raise


async def find_or_create_certification(
    db: AsyncSession, 
    certification_name: str, 
    issuing_organization: str,
    certification_type: str = "General",
    is_lifetime: bool = None
) -> LookupCertificationResponse:
    """
    Finds or creates a certification in tbl_cp_mcertifications.
    
    Parameters:
        db: Database session
        certification_name: Certification name
        issuing_organization: Organization issuing cert
        certification_type: Type of certification
        is_lifetime: Whether certification has no expiry
        
    Returns:
        LookupCertificationResponse with certification_id and certification_code
    """
    logger.debug(f"Looking up certification: {certification_name} from {issuing_organization}")
    
    # Query for existing certification (case-insensitive)
    result = await db.execute(
        text("""SELECT certification_id, certification_code FROM tbl_cp_mcertifications 
                WHERE LOWER(certification_name) = LOWER(:name) 
                AND LOWER(issuing_organization) = LOWER(:org)"""),
        {"name": certification_name, "org": issuing_organization}
    )
    existing = result.fetchone()
    
    if existing:
        logger.debug(f"Certification found: {existing[0]}")
        return LookupCertificationResponse(
            certification_id=existing[0],
            certification_name=certification_name,
            certification_code=existing[1],
            issuing_organization=issuing_organization,
            is_new=False
        )
    
    # Get next certification_id
    result = await db.execute(text("SELECT COALESCE(MAX(certification_id), 0) + 1 FROM tbl_cp_mcertifications"))
    next_id = result.scalar()
    
    # Generate certification_code
    org_code = issuing_organization.split()[0].upper()
    
    # Extract first letters from significant words in certification_name
    skip_words = {"of", "the", "and", "in", "for"}
    words = [w for w in certification_name.split() if w.lower() not in skip_words]
    cert_code = "".join(w[0].upper() for w in words if w)
    
    code = f"{org_code}-{cert_code}"
    
    # Check if code already exists, append _id if needed
    result = await db.execute(
        text("SELECT certification_id FROM tbl_cp_mcertifications WHERE certification_code = :code"),
        {"code": code}
    )
    if result.fetchone():
        code = f"{code}-{next_id}"
    
    # Insert new certification
    try:
        await db.execute(
            text("""INSERT INTO tbl_cp_mcertifications 
                    (certification_id, certification_name, certification_code, issuing_organization, certification_type, is_lifetime)
                    VALUES (:id, :name, :code, :org, :type, :lifetime)"""),
            {
                "id": next_id,
                "name": certification_name,
                "code": code,
                "org": issuing_organization,
                "type": certification_type,
                "lifetime": is_lifetime
            }
        )
        await db.commit()
        logger.debug(f"Certification created: {next_id}")
        return LookupCertificationResponse(
            certification_id=next_id,
            certification_name=certification_name,
            certification_code=code,
            issuing_organization=issuing_organization,
            is_new=True
        )
    except Exception as e:
        logger.error(f"Error creating certification: {e}")
        result = await db.execute(
            text("""SELECT certification_id, certification_code FROM tbl_cp_mcertifications 
                    WHERE LOWER(certification_name) = LOWER(:name) 
                    AND LOWER(issuing_organization) = LOWER(:org)"""),
            {"name": certification_name, "org": issuing_organization}
        )
        existing = result.fetchone()
        if existing:
            return LookupCertificationResponse(
                certification_id=existing[0],
                certification_name=certification_name,
                certification_code=existing[1],
                issuing_organization=issuing_organization,
                is_new=False
            )
        raise


async def find_or_create_college(db: AsyncSession, college_name: str) -> LookupCollegeResponse:
    """
    Finds or creates a college in tbl_cp_mcolleges.
    
    Parameters:
        db: Database session
        college_name: Name of the college
        
    Returns:
        LookupCollegeResponse with college_id
    """
    logger.debug(f"Looking up college: {college_name}")
    
    # Query for existing college (case-insensitive)
    result = await db.execute(
        text("SELECT college_id FROM tbl_cp_mcolleges WHERE LOWER(college_name) = LOWER(:name)"),
        {"name": college_name}
    )
    existing = result.fetchone()
    
    if existing:
        logger.debug(f"College found: {existing[0]}")
        return LookupCollegeResponse(college_id=existing[0], college_name=college_name, is_new=False)
    
    # Get next college_id
    result = await db.execute(text("SELECT COALESCE(MAX(college_id), 0) + 1 FROM tbl_cp_mcolleges"))
    next_id = result.scalar()
    
    # Insert new college with defaults
    try:
        await db.execute(
            text("""INSERT INTO tbl_cp_mcolleges 
                    (college_id, college_name, spoc_name, spoc_phone, spoc_email, tpo_name, tpo_phone, tpo_email,
                     student_coordinator_name, student_coordinator_phone, student_coordinator_email, priority)
                    VALUES (:id, :name, :spoc_name, :spoc_phone, :spoc_email, :tpo_name, :tpo_phone, :tpo_email,
                            :sc_name, :sc_phone, :sc_email, :priority)"""),
            {
                "id": next_id,
                "name": college_name,
                "spoc_name": "Not Assigned",
                "spoc_phone": "0000000000",
                "spoc_email": "noreply@college.com",
                "tpo_name": "Not Assigned",
                "tpo_phone": "0000000000",
                "tpo_email": "noreply@college.com",
                "sc_name": "Not Assigned",
                "sc_phone": "0000000000",
                "sc_email": "noreply@college.com",
                "priority": 5
            }
        )
        await db.commit()
        logger.debug(f"College created: {next_id}")
        return LookupCollegeResponse(college_id=next_id, college_name=college_name, is_new=True)
    except Exception as e:
        logger.error(f"Error creating college: {e}")
        result = await db.execute(
            text("SELECT college_id FROM tbl_cp_mcolleges WHERE LOWER(college_name) = LOWER(:name)"),
            {"name": college_name}
        )
        existing = result.fetchone()
        if existing:
            return LookupCollegeResponse(college_id=existing[0], college_name=college_name, is_new=False)
        raise


async def find_or_create_course(
    db: AsyncSession,
    course_name: str,
    specialization_name: str = "General"
) -> LookupCourseResponse:
    """
    Finds or creates a course in tbl_cp_mcourses.
    
    Parameters:
        db: Database session
        course_name: Course name
        specialization_name: Specialization within the course
        
    Returns:
        LookupCourseResponse with course_id, course_code, specialization_code
    """
    logger.debug(f"Looking up course: {course_name} - {specialization_name}")
    
    # Query for existing course (case-insensitive)
    result = await db.execute(
        text("""SELECT course_id, course_code, specialization_code FROM tbl_cp_mcourses 
                WHERE LOWER(course_name) = LOWER(:course_name) 
                AND LOWER(specialization_name) = LOWER(:spec_name)"""),
        {"course_name": course_name, "spec_name": specialization_name}
    )
    existing = result.fetchone()
    
    if existing:
        logger.debug(f"Course found: {existing[0]}")
        return LookupCourseResponse(
            course_id=existing[0],
            course_name=course_name,
            course_code=existing[1],
            specialization_name=specialization_name,
            specialization_code=existing[2],
            is_new=False
        )
    
    # Get next course_id
    result = await db.execute(text("SELECT COALESCE(MAX(course_id), 0) + 1 FROM tbl_cp_mcourses"))
    next_id = result.scalar()
    
    # Generate course_code
    course_code = COURSE_CODE_MAP.get(course_name.lower(), 
                                     "".join(w[0].upper() for w in course_name.split()))
    
    # Check if course_code already exists
    result = await db.execute(
        text("SELECT course_id FROM tbl_cp_mcourses WHERE course_code = :code"),
        {"code": course_code}
    )
    if result.fetchone():
        course_code = f"{course_code}2"
    
    # Generate specialization_code
    spec_code = "".join(w[0].upper() for w in specialization_name.split())
    
    # Check if spec_code already exists for this course
    result = await db.execute(
        text("SELECT course_id FROM tbl_cp_mcourses WHERE specialization_code = :code AND course_code = :course_code"),
        {"code": spec_code, "course_code": course_code}
    )
    if result.fetchone():
        spec_code = f"{spec_code}2"
    
    # Insert new course
    try:
        await db.execute(
            text("""INSERT INTO tbl_cp_mcourses 
                    (course_id, course_name, course_code, specialization_name, specialization_code)
                    VALUES (:id, :course_name, :course_code, :spec_name, :spec_code)"""),
            {
                "id": next_id,
                "course_name": course_name,
                "course_code": course_code,
                "spec_name": specialization_name,
                "spec_code": spec_code
            }
        )
        await db.commit()
        logger.debug(f"Course created: {next_id}")
        return LookupCourseResponse(
            course_id=next_id,
            course_name=course_name,
            course_code=course_code,
            specialization_name=specialization_name,
            specialization_code=spec_code,
            is_new=True
        )
    except Exception as e:
        logger.error(f"Error creating course: {e}")
        result = await db.execute(
            text("""SELECT course_id, course_code, specialization_code FROM tbl_cp_mcourses 
                    WHERE LOWER(course_name) = LOWER(:course_name) 
                    AND LOWER(specialization_name) = LOWER(:spec_name)"""),
            {"course_name": course_name, "spec_name": specialization_name}
        )
        existing = result.fetchone()
        if existing:
            return LookupCourseResponse(
                course_id=existing[0],
                course_name=course_name,
                course_code=existing[1],
                specialization_name=specialization_name,
                specialization_code=existing[2],
                is_new=False
            )
        raise


async def find_salutation(db: AsyncSession, value: str) -> LookupSalutationResponse:
    """
    Finds a salutation in tbl_cp_msalutation (read-only, does not create).
    
    Parameters:
        db: Database session
        value: Salutation value (e.g. "Mr.", "Ms.", "Dr.")
        
    Returns:
        LookupSalutationResponse with salutation_id or None if not found
    """
    logger.debug(f"Looking up salutation: {value}")
    
    # Query for existing salutation (case-insensitive)
    result = await db.execute(
        text("SELECT salutation_id FROM tbl_cp_msalutation WHERE LOWER(value) = LOWER(:value)"),
        {"value": value}
    )
    existing = result.fetchone()
    
    if existing:
        logger.debug(f"Salutation found: {existing[0]}")
        return LookupSalutationResponse(salutation_id=existing[0], value=value, found=True)
    
    logger.debug(f"Salutation not found: {value}")
    return LookupSalutationResponse(salutation_id=None, value=value, found=False)


async def find_pincode(db: AsyncSession, pincode: str) -> LookupPincodeResponse:
    """
    Finds a pincode in tbl_cp_mpincodes (read-only, does not create).
    
    Parameters:
        db: Database session
        pincode: Pincode string
        
    Returns:
        LookupPincodeResponse with pincode_id or None if not found
    """
    logger.debug(f"Looking up pincode: {pincode}")
    
    # Query for pincode
    result = await db.execute(
        text("SELECT pincode_id FROM tbl_cp_mpincodes WHERE pincode = :pincode"),
        {"pincode": pincode}
    )
    existing = result.fetchone()
    
    if existing:
        logger.debug(f"Pincode found: {existing[0]}")
        return LookupPincodeResponse(pincode_id=existing[0], pincode=pincode, found=True)
    
    logger.debug(f"Pincode not found: {pincode}")
    return LookupPincodeResponse(pincode_id=None, pincode=pincode, found=False)
