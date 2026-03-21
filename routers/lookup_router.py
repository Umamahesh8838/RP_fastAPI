from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from schemas.common_schema import SuccessResponse, ErrorResponse
from schemas.lookup_schema import (
    LookupSkillRequest, LookupSkillResponse,
    LookupLanguageRequest, LookupLanguageResponse,
    LookupInterestRequest, LookupInterestResponse,
    LookupCertificationRequest, LookupCertificationResponse,
    LookupCollegeRequest, LookupCollegeResponse,
    LookupCourseRequest, LookupCourseResponse,
    LookupSalutationRequest, LookupSalutationResponse,
    LookupPincodeRequest, LookupPincodeResponse
)
from utils.response_utils import success_response, error_response
from services import lookup_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/skill", response_model=SuccessResponse)
async def lookup_skill(request: LookupSkillRequest, db: AsyncSession = Depends(get_db)):
    """Finds or creates a skill."""
    try:
        result = await lookup_service.find_or_create_skill(db, request.name, request.complexity)
        return success_response(result.model_dump())
    except Exception as e:
        logger.error(f"Error in /lookup/skill: {e}")
        return error_response(str(e), status_code=400)


@router.post("/language", response_model=SuccessResponse)
async def lookup_language(request: LookupLanguageRequest, db: AsyncSession = Depends(get_db)):
    """Finds or creates a language."""
    try:
        result = await lookup_service.find_or_create_language(db, request.language_name)
        return success_response(result.model_dump())
    except Exception as e:
        logger.error(f"Error in /lookup/language: {e}")
        return error_response(str(e), status_code=400)


@router.post("/interest", response_model=SuccessResponse)
async def lookup_interest(request: LookupInterestRequest, db: AsyncSession = Depends(get_db)):
    """Finds or creates an interest."""
    try:
        result = await lookup_service.find_or_create_interest(db, request.name)
        return success_response(result.model_dump())
    except Exception as e:
        logger.error(f"Error in /lookup/interest: {e}")
        return error_response(str(e), status_code=400)


@router.post("/certification", response_model=SuccessResponse)
async def lookup_certification(request: LookupCertificationRequest, db: AsyncSession = Depends(get_db)):
    """Finds or creates a certification."""
    try:
        result = await lookup_service.find_or_create_certification(
            db,
            request.certification_name,
            request.issuing_organization,
            request.certification_type or "General",
            request.is_lifetime
        )
        return success_response(result.model_dump())
    except Exception as e:
        logger.error(f"Error in /lookup/certification: {e}")
        return error_response(str(e), status_code=400)


@router.post("/college", response_model=SuccessResponse)
async def lookup_college(request: LookupCollegeRequest, db: AsyncSession = Depends(get_db)):
    """Finds or creates a college."""
    try:
        result = await lookup_service.find_or_create_college(db, request.college_name)
        return success_response(result.model_dump())
    except Exception as e:
        logger.error(f"Error in /lookup/college: {e}")
        return error_response(str(e), status_code=400)


@router.post("/course", response_model=SuccessResponse)
async def lookup_course(request: LookupCourseRequest, db: AsyncSession = Depends(get_db)):
    """Finds or creates a course."""
    try:
        result = await lookup_service.find_or_create_course(
            db,
            request.course_name,
            request.specialization_name or "General"
        )
        return success_response(result.model_dump())
    except Exception as e:
        logger.error(f"Error in /lookup/course: {e}")
        return error_response(str(e), status_code=400)


@router.post("/salutation", response_model=SuccessResponse)
async def lookup_salutation(request: LookupSalutationRequest, db: AsyncSession = Depends(get_db)):
    """Looks up a salutation (read-only, does not create)."""
    try:
        result = await lookup_service.find_salutation(db, request.value)
        return success_response(result.model_dump())
    except Exception as e:
        logger.error(f"Error in /lookup/salutation: {e}")
        return error_response(str(e), status_code=400)


@router.post("/pincode", response_model=SuccessResponse)
async def lookup_pincode(request: LookupPincodeRequest, db: AsyncSession = Depends(get_db)):
    """Looks up a pincode (read-only, does not create)."""
    try:
        result = await lookup_service.find_pincode(db, request.pincode)
        return success_response(result.model_dump())
    except Exception as e:
        logger.error(f"Error in /lookup/pincode: {e}")
        return error_response(str(e), status_code=400)
