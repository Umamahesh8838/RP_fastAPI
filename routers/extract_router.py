from fastapi import APIRouter, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from fastapi import Depends
from schemas.common_schema import SuccessResponse, ErrorResponse
from schemas.extract_schema import PDFExtractResponse, DocxExtractResponse
from utils.response_utils import success_response, error_response
from services import extract_service
from config import get_settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.post(
    "/pdf-to-text",
    response_model=SuccessResponse,
    responses={400: {"model": ErrorResponse}, 413: {"model": ErrorResponse}}
)
async def extract_pdf_to_text(file: UploadFile = File(...)):
    """
    Extracts text from a PDF resume file.
    
    Parameters:
        file: PDF file to extract text from
        
    Returns:
        Success response with extracted text, page count, and character count
    """
    try:
        # Validate file
        if not file:
            return error_response("No file provided", status_code=400)
        
        if not file.filename.lower().endswith('.pdf'):
            return error_response("File must be a PDF", detail="Only .pdf files are supported", status_code=400)
        
        # Check file size
        file_bytes = await file.read()
        file_size_mb = len(file_bytes) / (1024 * 1024)
        if file_size_mb > settings.max_file_size_mb:
            return error_response(
                f"File too large",
                detail=f"Max size is {settings.max_file_size_mb}MB",
                status_code=413
            )
        
        # Extract
        result = extract_service.extract_text_from_pdf(file_bytes)
        return success_response(result)
        
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        logger.error(f"Unexpected error in /extract/pdf-to-text: {e}")
        return error_response("Internal server error", detail=str(e), status_code=500)


@router.post(
    "/docx-to-text",
    response_model=SuccessResponse,
    responses={400: {"model": ErrorResponse}, 413: {"model": ErrorResponse}}
)
async def extract_docx_to_text(file: UploadFile = File(...)):
    """
    Extracts text from a .docx Word resume file.
    
    Parameters:
        file: DOCX file to extract text from
        
    Returns:
        Success response with extracted text, paragraph count, and character count
    """
    try:
        # Validate file
        if not file:
            return error_response("No file provided", status_code=400)
        
        if not file.filename.lower().endswith('.docx'):
            return error_response("File must be a DOCX", detail="Only .docx files are supported", status_code=400)
        
        # Check file size
        file_bytes = await file.read()
        file_size_mb = len(file_bytes) / (1024 * 1024)
        if file_size_mb > settings.max_file_size_mb:
            return error_response(
                f"File too large",
                detail=f"Max size is {settings.max_file_size_mb}MB",
                status_code=413
            )
        
        # Extract
        result = extract_service.extract_text_from_docx(file_bytes)
        return success_response(result)
        
    except ValueError as e:
        return error_response(str(e), status_code=422)
    except Exception as e:
        logger.error(f"Unexpected error in /extract/docx-to-text: {e}")
        return error_response("Internal server error", detail=str(e), status_code=500)
