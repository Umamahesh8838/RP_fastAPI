from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from schemas.common_schema import SuccessResponse, ErrorResponse
from schemas.parse_schema import SaveConfirmedRequest
from utils.response_utils import success_response, error_response
from services import orchestrator_service
from config import get_settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.post(
    "/upload",
    response_model=SuccessResponse,
    responses={400: {"model": ErrorResponse}, 413: {"model": ErrorResponse}}
)
async def upload_resume(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """
    Complete resume upload and processing pipeline.
    Extracts text, parses with LLM, and fills the database.
    
    Parameters:
        file: Resume file (PDF or image)
        db: Database session
        
    Returns:
        Success response with student_id, resume_hash, and summary of saved records
    """
    try:
        # Validate file
        if not file:
            return error_response("No file provided", status_code=400)
        
        if not file.filename:
            return error_response("File must have a name", status_code=400)
        
        # Check file extension
        file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
        allowed_exts = settings.allowed_extensions_list
        if file_ext not in allowed_exts:
            return error_response(
                "Unsupported file type",
                detail=f"Allowed types: {', '.join(allowed_exts)}",
                status_code=400
            )
        
        # Check file size
        file_bytes = await file.read()
        file_size_mb = len(file_bytes) / (1024 * 1024)
        if file_size_mb > settings.max_file_size_mb:
            return error_response(
                f"File too large",
                detail=f"Max size is {settings.max_file_size_mb}MB",
                status_code=413
            )
        
        # Run full pipeline
        result = await orchestrator_service.run_full_pipeline(db, file_bytes, file.filename)
        
        return success_response(result)
        
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        logger.error(f"Unexpected error in /resume/upload: {e}")
        return error_response("Internal server error", detail=str(e), status_code=500)


@router.post(
    "/parse-preview",
    response_model=SuccessResponse,
    responses={400: {"model": ErrorResponse}, 413: {"model": ErrorResponse}}
)
async def parse_resume_preview(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """
    Preview resume parsing without saving to database.
    Extracts text, checks for duplicates, and parses with LLM.
    User can review the parsed data before confirming save.
    
    Parameters:
        file: Resume file (PDF or DOCX)
        db: Database session
        
    Returns:
        Success response with resume_hash, already_exists flag, and parsed data
    """
    try:
        # Validate file
        if not file:
            return error_response("No file provided", status_code=400)
        
        if not file.filename:
            return error_response("File must have a name", status_code=400)
        
        # Check file extension
        file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
        allowed_exts = settings.allowed_extensions_list
        if file_ext not in allowed_exts:
            return error_response(
                "Unsupported file type",
                detail=f"Allowed types: {', '.join(allowed_exts)}",
                status_code=400
            )
        
        # Check file size
        file_bytes = await file.read()
        file_size_mb = len(file_bytes) / (1024 * 1024)
        if file_size_mb > settings.max_file_size_mb:
            return error_response(
                f"File too large",
                detail=f"Max size is {settings.max_file_size_mb}MB",
                status_code=413
            )
        
        # Run parse preview (steps 1-3 only, no database save)
        result = await orchestrator_service.parse_resume_preview(db, file_bytes, file.filename)
        
        return success_response(result)
        
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        logger.error(f"Unexpected error in /resume/parse-preview: {e}")
        return error_response("Internal server error", detail=str(e), status_code=500)


@router.post(
    "/save-confirmed",
    response_model=SuccessResponse,
    responses={400: {"model": ErrorResponse}}
)
async def save_confirmed_resume(request: SaveConfirmedRequest, db: AsyncSession = Depends(get_db)):
    """
    Save a confirmed/edited ParsedResume to the database.
    Called after user has reviewed the parsed data from /parse-preview.
    
    Parameters:
        request: SaveConfirmedRequest with resume_hash and parsed data
        db: Database session
        
    Returns:
        Success response with student_id, resume_hash, and summary of saved records
    """
    try:
        # Validate request
        if not request.resume_hash:
            return error_response("resume_hash is required", status_code=400)
        
        if not request.parsed:
            return error_response("parsed data is required", status_code=400)
        
        # Save confirmed resume (steps 4-15 of pipeline)
        result = await orchestrator_service.save_confirmed_resume(
            db, 
            request.resume_hash, 
            request.parsed
        )
        
        return success_response(result)
        
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        logger.error(f"Unexpected error in /resume/save-confirmed: {e}")
        return error_response("Internal server error", detail=str(e), status_code=500)
