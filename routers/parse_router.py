from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from fastapi import Depends
from schemas.common_schema import SuccessResponse, ErrorResponse
from schemas.parse_schema import ParseResumeRequest, ParseResumeResponse
from utils.response_utils import success_response, error_response
from utils.hash_utils import compute_resume_hash
from services import llm_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/resume",
    response_model=SuccessResponse,
    responses={400: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}
)
async def parse_resume(request: ParseResumeRequest):
    """
    Parses resume text using LLM (2 passes: extraction + gap checking).
    
    Parameters:
        request: ParseResumeRequest with resume_text
        
    Returns:
        Success response with parsed resume data and SHA-256 hash
    """
    try:
        # Validate input
        if not request.resume_text or len(request.resume_text.strip()) < 100:
            return error_response(
                "Resume text too short",
                detail="Minimum 100 characters required",
                status_code=422
            )
        
        # Parse resume with LLM
        parsed = await llm_service.parse_resume_text(request.resume_text)
        
        # Compute hash
        resume_hash = compute_resume_hash(request.resume_text)
        
        response = ParseResumeResponse(
            parsed=parsed,
            resume_hash=resume_hash
        )
        
        return success_response(response.model_dump())
        
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        logger.error(f"Unexpected error in /parse/resume: {e}")
        return error_response("Internal server error", detail=str(e), status_code=500)
