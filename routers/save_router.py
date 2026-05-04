from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from pydantic import BaseModel
from schemas.common_schema import SuccessResponse, ErrorResponse
from schemas.student_schema import SaveStudentRequest, SaveStudentResponse
from schemas.education_schema import SaveSchoolRequest, SaveEducationRequest
from schemas.workexp_schema import SaveWorkExpRequest, SaveWorkExpResponse
from schemas.project_schema import SaveProjectRequest, SaveProjectResponse, SaveProjectSkillRequest
from schemas.address_schema import SaveAddressRequest, SaveAddressResponse
from utils.response_utils import success_response, error_response
from services import save_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class SaveStudentSkillRequest(BaseModel):
    student_id: int
    skill_id: int


class SaveStudentLanguageRequest(BaseModel):
    student_id: int
    language_id: int


class SaveStudentInterestRequest(BaseModel):
    student_id: int
    interest_id: int


class SaveStudentCertificationRequest(BaseModel):
    student_id: int
    certification_id: int
    issue_date: str = None
    expiry_date: str = None
    certificate_url: str = None
    credential_id: str = None


@router.post("/student", response_model=SuccessResponse)
def save_student_endpoint(request: SaveStudentRequest, db: Session = Depends(get_db)):
    """Saves a student record."""
    try:
        result = save_service.save_student(db, request)
        return success_response(result.model_dump())
    except Exception as e:
        logger.error(f"Error in /save/student: {e}")
        return error_response(str(e), status_code=400)


@router.post("/school", response_model=SuccessResponse)
def save_school_endpoint(request: SaveSchoolRequest, db: Session = Depends(get_db)):
    """Saves a school record."""
    try:
        result = save_service.save_school(db, request)
        return success_response(result)
    except Exception as e:
        logger.error(f"Error in /save/school: {e}")
        return error_response(str(e), status_code=400)


@router.post("/education", response_model=SuccessResponse)
def save_education_endpoint(request: SaveEducationRequest, db: Session = Depends(get_db)):
    """Saves an education record."""
    try:
        result = save_service.save_education(db, request)
        return success_response(result)
    except Exception as e:
        logger.error(f"Error in /save/education: {e}")
        return error_response(str(e), status_code=400)


@router.post("/workexp", response_model=SuccessResponse)
def save_workexp_endpoint(request: SaveWorkExpRequest, db: Session = Depends(get_db)):
    """Saves a work experience record."""
    try:
        result = save_service.save_workexp(db, request)
        return success_response(result.model_dump())
    except Exception as e:
        logger.error(f"Error in /save/workexp: {e}")
        return error_response(str(e), status_code=400)


@router.post("/project", response_model=SuccessResponse)
def save_project_endpoint(request: SaveProjectRequest, db: Session = Depends(get_db)):
    """Saves a project record."""
    try:
        result = save_service.save_project(db, request)
        return success_response(result.model_dump())
    except Exception as e:
        logger.error(f"Error in /save/project: {e}")
        return error_response(str(e), status_code=400)


@router.post("/project-skill", response_model=SuccessResponse)
def save_project_skill_endpoint(request: SaveProjectSkillRequest, db: Session = Depends(get_db)):
    """Saves a project-skill relationship."""
    try:
        result = save_service.save_project_skill(db, request.project_id, request.skill_id)
        return success_response(result)
    except Exception as e:
        logger.error(f"Error in /save/project-skill: {e}")
        return error_response(str(e), status_code=400)


@router.post("/student-skill", response_model=SuccessResponse)
def save_student_skill_endpoint(request: SaveStudentSkillRequest, db: Session = Depends(get_db)):
    """Saves a student-skill relationship."""
    try:
        result = save_service.save_student_skill(db, request.student_id, request.skill_id)
        return success_response(result)
    except Exception as e:
        logger.error(f"Error in /save/student-skill: {e}")
        return error_response(str(e), status_code=400)


@router.post("/student-language", response_model=SuccessResponse)
def save_student_language_endpoint(request: SaveStudentLanguageRequest, db: Session = Depends(get_db)):
    """Saves a student-language relationship."""
    try:
        result = save_service.save_student_language(db, request.student_id, request.language_id)
        return success_response(result)
    except Exception as e:
        logger.error(f"Error in /save/student-language: {e}")
        return error_response(str(e), status_code=400)


@router.post("/student-interest", response_model=SuccessResponse)
def save_student_interest_endpoint(request: SaveStudentInterestRequest, db: Session = Depends(get_db)):
    """Saves a student-interest relationship."""
    try:
        result = save_service.save_student_interest(db, request.student_id, request.interest_id)
        return success_response(result)
    except Exception as e:
        logger.error(f"Error in /save/student-interest: {e}")
        return error_response(str(e), status_code=400)


@router.post("/student-certification", response_model=SuccessResponse)
def save_student_certification_endpoint(request: SaveStudentCertificationRequest, db: Session = Depends(get_db)):
    """Saves a student-certification relationship."""
    try:
        data = {
            "student_id": request.student_id,
            "certification_id": request.certification_id,
            "issue_date": request.issue_date,
            "expiry_date": request.expiry_date,
            "certificate_url": request.certificate_url,
            "credential_id": request.credential_id
        }
        result = save_service.save_student_certification(db, data)
        return success_response(result)
    except Exception as e:
        logger.error(f"Error in /save/student-certification: {e}")
        return error_response(str(e), status_code=400)


@router.post("/address", response_model=SuccessResponse)
def save_address_endpoint(request: SaveAddressRequest, db: Session = Depends(get_db)):
    """Saves an address record."""
    try:
        result = save_service.save_address(db, request)
        return success_response(result.model_dump())
    except Exception as e:
        logger.error(f"Error in /save/address: {e}")
        return error_response(str(e), status_code=400)
