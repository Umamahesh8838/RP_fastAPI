from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging
from schemas.parse_schema import ParsedResume
from utils.hash_utils import compute_resume_hash
from utils.date_utils import safe_date
from services import extract_service, llm_service, lookup_service, save_service
from schemas.student_schema import SaveStudentRequest
from schemas.education_schema import SaveSchoolRequest, SaveEducationRequest
from schemas.workexp_schema import SaveWorkExpRequest
from schemas.project_schema import SaveProjectRequest
from schemas.address_schema import SaveAddressRequest
from datetime import date

logger = logging.getLogger(__name__)


async def run_full_pipeline(db: AsyncSession, file_bytes: bytes, filename: str) -> dict:
    """
    Runs the complete 15-step resume processing pipeline.
    
    Parameters:
        db: Database session
        file_bytes: Resume file contents as bytes
        filename: Original filename (for extension detection)
        
    Returns:
        dict with student_id, summary, warnings
        
    Raises:
        ValueError: If critical steps fail (1, 2, 3, or 4)
    """
    logger.info("=== STARTING FULL RESUME PIPELINE ===")
    
    warnings = []
    summary = {
        "schools_saved": 0,
        "educations_saved": 0,
        "workexps_saved": 0,
        "projects_saved": 0,
        "skills_saved": 0,
        "languages_saved": 0,
        "certifications_saved": 0,
        "interests_saved": 0,
        "addresses_saved": 0
    }
    
    # STEP 1 — Extract text
    logger.info("STEP 1 — Extract text")
    try:
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        if file_ext == 'pdf':
            extract_result = await extract_service.extract_text_from_pdf(file_bytes)
        elif file_ext == 'docx':
            extract_result = await extract_service.extract_text_from_docx(file_bytes)
        else:
            raise ValueError(f"Unsupported file type. Please upload a PDF or DOCX file.")
        
        resume_text = extract_result["text"]
        logger.info(f"Step 1 complete: extracted {extract_result['char_count']} chars")
    except Exception as e:
        logger.error(f"Step 1 failed: {str(e)}")
        raise ValueError(f"Text extraction failed: {str(e)}")
    
    # STEP 2 — Duplicate check
    logger.info("STEP 2 — Duplicate check")
    try:
        resume_hash = compute_resume_hash(resume_text)
        result = await db.execute(
            text("SELECT student_id FROM tbl_cp_resume_hashes WHERE hash = :hash"),
            {"hash": resume_hash}
        )
        existing_hash = result.fetchone()
        
        if existing_hash:
            logger.info(f"Step 2: Resume already processed, student_id={existing_hash[0]}")
            return {
                "student_id": existing_hash[0],
                "resume_hash": resume_hash,
                "already_existed": True,
                "message": "Resume already processed"
            }
        
        logger.info("Step 2 complete: no duplicate found")
    except Exception as e:
        logger.error(f"Step 2 failed: {str(e)}")
        raise ValueError(f"Duplicate check failed: {str(e)}")
    
    # STEP 3 — LLM Parse (2 passes happen here)
    logger.info("STEP 3 — LLM Parse (2 passes)")
    try:
        parsed = await llm_service.parse_resume_text(resume_text)
        logger.info("Step 3 complete: LLM parsing done")
    except Exception as e:
        logger.error(f"Step 3 failed: {str(e)}")
        raise ValueError(f"LLM parsing failed: {str(e)}")
    
    # STEP 4 — Save student core record
    logger.info("STEP 4 — Save student core record")
    try:
        salutation_id = None
        if parsed.salutation:
            sal_result = await lookup_service.find_salutation(db, parsed.salutation)
            if sal_result.found:
                salutation_id = sal_result.salutation_id
        
        student_result = await save_service.save_student(
            db,
            SaveStudentRequest(
                salutation_id=salutation_id,
                first_name=parsed.first_name,
                middle_name=parsed.middle_name,
                last_name=parsed.last_name,
                email=parsed.email,
                alt_email=parsed.alt_email,
                contact_number=parsed.contact_number,
                alt_contact_number=parsed.alt_contact_number,
                linkedin_url=parsed.linkedin_url,
                github_url=parsed.github_url,
                portfolio_url=parsed.portfolio_url,
                date_of_birth=parsed.date_of_birth,
                current_city=parsed.current_city,
                gender=parsed.gender
            )
        )
        
        student_id = student_result.student_id
        already_existed = student_result.already_exists
        logger.info(f"Step 4 complete: student_id={student_id}, already_existed={already_existed}")
    except Exception as e:
        logger.error(f"Step 4 failed: {str(e)}")
        raise ValueError(f"Student save failed: {str(e)}")
    
    # STEP 5 — Save school records
    logger.info("STEP 5 — Save school records")
    try:
        for school_item in parsed.school:
            if not school_item.standard:
                continue
            try:
                await save_service.save_school(
                    db,
                    SaveSchoolRequest(
                        student_id=student_id,
                        standard=school_item.standard,
                        board=school_item.board,
                        school_name=school_item.school_name,
                        percentage=school_item.percentage,
                        passing_year=school_item.passing_year
                    )
                )
                summary["schools_saved"] += 1
            except Exception as e:
                logger.warning(f"Failed to save school: {str(e)}")
                warnings.append(f"School save failed: {str(e)}")
        
        logger.info(f"Step 5 complete: {summary['schools_saved']} school records saved")
    except Exception as e:
        logger.warning(f"Step 5 warning: {str(e)}")
    
    # STEP 6 — Save college education
    logger.info("STEP 6 — Save college education")
    try:
        for edu_item in parsed.education:
            if not edu_item.college_name or not edu_item.course_name:
                continue
            try:
                college_result = await lookup_service.find_or_create_college(db, edu_item.college_name)
                college_id = college_result.college_id
                
                course_result = await lookup_service.find_or_create_course(
                    db,
                    edu_item.course_name,
                    edu_item.specialization_name or "General"
                )
                course_id = course_result.course_id
                
                await save_service.save_education(
                    db,
                    SaveEducationRequest(
                        student_id=student_id,
                        college_id=college_id,
                        course_id=course_id,
                        start_year=edu_item.start_year,
                        end_year=edu_item.end_year,
                        cgpa=edu_item.cgpa,
                        percentage=edu_item.percentage
                    )
                )
                summary["educations_saved"] += 1
            except Exception as e:
                logger.warning(f"Failed to save education: {str(e)}")
                warnings.append(f"Education save failed: {str(e)}")
        
        logger.info(f"Step 6 complete: {summary['educations_saved']} education records saved")
    except Exception as e:
        logger.warning(f"Step 6 warning: {str(e)}")
    
    # STEP 7 — Save work experience
    logger.info("STEP 7 — Save work experience")
    try:
        workexp_map = {}
        for exp_item in parsed.workexp:
            if not exp_item.company_name:
                continue
            try:
                result = await save_service.save_workexp(
                    db,
                    SaveWorkExpRequest(
                        student_id=student_id,
                        company_name=exp_item.company_name,
                        company_location=exp_item.company_location,
                        designation=exp_item.designation,
                        employment_type=exp_item.employment_type,
                        start_date=exp_item.start_date,
                        end_date=exp_item.end_date,
                        is_current=exp_item.is_current
                    )
                )
                workexp_map[exp_item.company_name] = result.workexp_id
                summary["workexps_saved"] += 1
            except Exception as e:
                logger.warning(f"Failed to save workexp: {str(e)}")
                warnings.append(f"Work experience save failed: {str(e)}")
        
        logger.info(f"Step 7 complete: {summary['workexps_saved']} workexp records saved")
    except Exception as e:
        logger.warning(f"Step 7 warning: {str(e)}")
        workexp_map = {}
    
    # STEP 8 — Save projects + project skills
    logger.info("STEP 8 — Save projects + project skills")
    try:
        for proj_item in parsed.projects:
            if not proj_item.project_title:
                continue
            try:
                # Resolve workexp_id
                linked_workexp_id = None
                if proj_item.workexp_company_name:
                    linked_workexp_id = workexp_map.get(proj_item.workexp_company_name, None)
                
                proj_result = await save_service.save_project(
                    db,
                    SaveProjectRequest(
                        student_id=student_id,
                        workexp_id=linked_workexp_id,
                        project_title=proj_item.project_title,
                        project_description=proj_item.project_description,
                        achievements=proj_item.achievements,
                        project_start_date=proj_item.project_start_date,
                        project_end_date=proj_item.project_end_date
                    )
                )
                project_id = proj_result.project_id
                summary["projects_saved"] += 1
                
                # Save skills used in this project
                for skill_name in proj_item.skills_used:
                    if not skill_name:
                        continue
                    try:
                        skill_result = await lookup_service.find_or_create_skill(db, skill_name, "Intermediate")
                        await save_service.save_project_skill(db, project_id, skill_result.skill_id)
                    except Exception as e:
                        logger.warning(f"Failed to save project skill: {str(e)}")
                        warnings.append(f"Project skill save failed: {str(e)}")
            except Exception as e:
                logger.warning(f"Failed to save project: {str(e)}")
                warnings.append(f"Project save failed: {str(e)}")
        
        logger.info(f"Step 8 complete: {summary['projects_saved']} projects saved")
    except Exception as e:
        logger.warning(f"Step 8 warning: {str(e)}")
    
    # STEP 9 — Save student skills
    logger.info("STEP 9 — Save student skills")
    try:
        for skill_item in parsed.skills:
            if not skill_item.name:
                continue
            try:
                skill_result = await lookup_service.find_or_create_skill(
                    db, skill_item.name, skill_item.complexity or "Intermediate"
                )
                await save_service.save_student_skill(db, student_id, skill_result.skill_id)
                summary["skills_saved"] += 1
            except Exception as e:
                logger.warning(f"Failed to save student skill: {str(e)}")
                warnings.append(f"Student skill save failed: {str(e)}")
        
        logger.info(f"Step 9 complete: {summary['skills_saved']} skills linked to student")
    except Exception as e:
        logger.warning(f"Step 9 warning: {str(e)}")
    
    # STEP 10 — Save languages
    logger.info("STEP 10 — Save languages")
    try:
        for lang_item in parsed.languages:
            if not lang_item.language_name:
                continue
            try:
                lang_result = await lookup_service.find_or_create_language(db, lang_item.language_name)
                await save_service.save_student_language(db, student_id, lang_result.language_id)
                summary["languages_saved"] += 1
            except Exception as e:
                logger.warning(f"Failed to save student language: {str(e)}")
                warnings.append(f"Language save failed: {str(e)}")
        
        logger.info(f"Step 10 complete: {summary['languages_saved']} languages linked")
    except Exception as e:
        logger.warning(f"Step 10 warning: {str(e)}")
    
    # STEP 11 — Save certifications
    logger.info("STEP 11 — Save certifications")
    try:
        for cert_item in parsed.certifications:
            if not cert_item.certification_name or not cert_item.issuing_organization:
                continue
            try:
                cert_result = await lookup_service.find_or_create_certification(
                    db,
                    cert_item.certification_name,
                    cert_item.issuing_organization,
                    cert_item.certification_type or "General",
                    cert_item.is_lifetime
                )
                await save_service.save_student_certification(
                    db,
                    {
                        "student_id": student_id,
                        "certification_id": cert_result.certification_id,
                        "issue_date": cert_item.issue_date,
                        "expiry_date": cert_item.expiry_date,
                        "certificate_url": cert_item.certificate_url,
                        "credential_id": cert_item.credential_id
                    }
                )
                summary["certifications_saved"] += 1
            except Exception as e:
                logger.warning(f"Failed to save certification: {str(e)}")
                warnings.append(f"Certification save failed: {str(e)}")
        
        logger.info(f"Step 11 complete: {summary['certifications_saved']} certifications saved")
    except Exception as e:
        logger.warning(f"Step 11 warning: {str(e)}")
    
    # STEP 12 — Save interests
    logger.info("STEP 12 — Save interests")
    try:
        for interest_item in parsed.interests:
            if not interest_item.name:
                continue
            try:
                interest_result = await lookup_service.find_or_create_interest(db, interest_item.name)
                await save_service.save_student_interest(db, student_id, interest_result.interest_id)
                summary["interests_saved"] += 1
            except Exception as e:
                logger.warning(f"Failed to save student interest: {str(e)}")
                warnings.append(f"Interest save failed: {str(e)}")
        
        logger.info(f"Step 12 complete: {summary['interests_saved']} interests linked")
    except Exception as e:
        logger.warning(f"Step 12 warning: {str(e)}")
    
    # STEP 13 — Save addresses
    logger.info("STEP 13 — Save addresses")
    try:
        for addr_item in parsed.addresses:
            if not addr_item.address_line_1 or not addr_item.pincode:
                continue
            try:
                pincode_result = await lookup_service.find_pincode(db, addr_item.pincode)
                if not pincode_result.found:
                    logger.warning(f"Pincode {addr_item.pincode} not found in database")
                    warnings.append(f"Pincode {addr_item.pincode} not found. Address skipped.")
                    continue
                
                await save_service.save_address(
                    db,
                    SaveAddressRequest(
                        student_id=student_id,
                        address_line_1=addr_item.address_line_1,
                        address_line_2=addr_item.address_line_2,
                        landmark=addr_item.landmark,
                        pincode_id=pincode_result.pincode_id,
                        address_type=addr_item.address_type or "current"
                    )
                )
                summary["addresses_saved"] += 1
            except Exception as e:
                logger.warning(f"Failed to save address: {str(e)}")
                warnings.append(f"Address save failed: {str(e)}")
        
        logger.info(f"Step 13 complete: {summary['addresses_saved']} addresses saved")
    except Exception as e:
        logger.warning(f"Step 13 warning: {str(e)}")
    
    # STEP 14 — Store resume hash
    logger.info("STEP 14 — Store resume hash")
    try:
        await db.execute(
            text("INSERT INTO tbl_cp_resume_hashes (hash, student_id) VALUES (:hash, :student_id)"),
            {"hash": resume_hash, "student_id": student_id}
        )
        await db.commit()
        logger.info("Step 14 complete: resume hash stored")
    except Exception as e:
        logger.warning(f"Step 14 warning: {str(e)}")
        warnings.append(f"Resume hash storage failed: {str(e)}")
    
    # STEP 15 — Return final summary
    logger.info("STEP 15 — Return final summary")
    logger.info(f"=== PIPELINE COMPLETE ===")
    
    return {
        "student_id": student_id,
        "resume_hash": resume_hash,
        "already_existed": already_existed,
        "summary": summary,
        "warnings": warnings
    }
