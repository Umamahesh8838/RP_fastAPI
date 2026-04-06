from fastapi import APIRouter, UploadFile, File, Depends, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from database import get_db
from schemas.common_schema import SuccessResponse, ErrorResponse
from schemas.parse_schema import SaveConfirmedRequest
from utils.response_utils import success_response, error_response
from utils import cache_utils
from utils.hash_utils import compute_resume_hash
from services import orchestrator_service, extract_service, llm_service
from config import get_settings
import asyncio
import json
import logging
import os
import uuid

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
    "/parse-with-progress",
    responses={400: {"model": ErrorResponse}, 413: {"model": ErrorResponse}},
    summary="Parse resume with streaming progress (SSE)"
)
async def parse_with_progress(request: Request, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """
    Streams parsing progress updates via Server-Sent Events to avoid frontend timeouts.
    """
    # Basic validation before starting stream
    if not file:
        return error_response("No file provided", status_code=400)
    if not file.filename:
        return error_response("File must have a name", status_code=400)

    file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    allowed_exts = settings.allowed_extensions_list
    if file_ext not in allowed_exts:
        return error_response(
            "Unsupported file type",
            detail=f"Allowed types: {', '.join(allowed_exts)}",
            status_code=400
        )

    # READ FILE IMMEDIATELY before streaming (critical!)
    try:
        file_bytes = await file.read()
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return error_response("Failed to read file", detail=str(e), status_code=400)
    
    file_size_mb = len(file_bytes) / (1024 * 1024)
    if file_size_mb > settings.max_file_size_mb:
        return error_response(
            "File too large",
            detail=f"Max size is {settings.max_file_size_mb}MB",
            status_code=413
        )

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "*",
        "X-Accel-Buffering": "no",
    }

    async def event_stream():
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        async def emit(event_type: str, payload: dict):
            await queue.put(f"event: {event_type}\ndata: {json.dumps(payload)}\n\n")

        async def producer():
            try:
                await emit("progress", {"step": 1, "message": "Reading resume file...", "percent": 5})

                file_size_mb_check = len(file_bytes) / (1024 * 1024)
                if file_size_mb_check > settings.max_file_size_mb:
                    await emit("error", {"message": f"File too large. Max size is {settings.max_file_size_mb}MB"})
                    return

                await emit("progress", {"step": 2, "message": "Extracting text from document...", "percent": 10})
                if file_ext == "pdf":
                    extract_result = await extract_service.extract_text_from_pdf(file_bytes)
                elif file_ext == "docx":
                    extract_result = await extract_service.extract_text_from_docx(file_bytes)
                else:
                    await emit("error", {"message": "Unsupported file type"})
                    return

                resume_text = extract_result.get("text", "")

                await emit("progress", {"step": 3, "message": "Checking for duplicate resume...", "percent": 15})
                resume_hash = compute_resume_hash(resume_text)
                result = await db.execute(
                    text("SELECT student_id FROM tbl_cp_resume_hashes WHERE hash = :hash"),
                    {"hash": resume_hash}
                )
                existing_hash = result.fetchone()
                already_exists = existing_hash is not None

                cached = cache_utils.load_from_cache(resume_hash)
                if cached:
                    logger.info("[CACHE HIT] Returning cached result, skipping LLM")
                    await emit("progress", {"step": 8, "message": "Saving parsed data to cache...", "percent": 90})
                    cached["already_exists"] = already_exists
                    cached["resume_hash"] = resume_hash
                    await emit("complete", {
                        "step": 9,
                        "message": "Resume parsed successfully!",
                        "percent": 100,
                        "resume_hash": resume_hash,
                        "parsed": cached.get("parsed", {}),
                        "already_exists": already_exists
                    })
                    return

                await emit("progress", {"step": 4, "message": "Starting AI analysis (Pass 1 of 2)... This takes 60-90 seconds", "percent": 20})
                await emit("progress", {"step": 5, "message": "AI is reading your resume line by line...", "percent": 40})

                llm_task = asyncio.create_task(llm_service.parse_resume_text(resume_text))
                # Keep-alive heartbeats while LLM runs
                while not llm_task.done():
                    await asyncio.sleep(5)
                    if llm_task.done():
                        break
                    await emit("progress", {"step": 5, "message": "AI is reading your resume line by line...", "percent": 45})

                parsed_result = await llm_task

                await emit("progress", {"step": 6, "message": "Pass 1 complete. Starting quality check (Pass 2 of 2)...", "percent": 60})
                await emit("progress", {"step": 7, "message": "Verifying extracted data for accuracy...", "percent": 80})

                parsed_dict = parsed_result.model_dump() if hasattr(parsed_result, "model_dump") else parsed_result
                cache_data = {
                    "resume_hash": resume_hash,
                    "already_exists": already_exists,
                    "parsed": parsed_dict
                }

                cache_utils.save_to_cache(resume_hash, cache_data)
                await emit("progress", {"step": 8, "message": "Saving parsed data to cache...", "percent": 90})

                await emit("complete", {
                    "step": 9,
                    "message": "Resume parsed successfully!",
                    "percent": 100,
                    "resume_hash": resume_hash,
                    "parsed": parsed_dict,
                    "already_exists": already_exists
                })
            except Exception as e:
                logger.error(f"Unexpected error in /resume/parse-with-progress: {e}")
                await emit("error", {"message": str(e)})
            finally:
                await queue.put(None)

        producer_task = asyncio.create_task(producer())

        while True:
            item = await queue.get()
            if item is None:
                break
            yield item

        await producer_task

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)


@router.get(
    "/get-cached/{resume_hash}",
    response_model=SuccessResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_cached_resume(resume_hash: str):
    """
    Retrieve cached parsed resume data by resume_hash.
    Useful when the parse-preview response was lost.
    """
    data = cache_utils.load_from_cache(resume_hash)
    if data:
        return success_response(data)
    return error_response(
        "No cached data found for this resume. Please upload the resume again.",
        status_code=404
    )


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


@router.get(
    "/cache-status",
    response_model=SuccessResponse
)
async def cache_status():
    """Returns current cached resume hashes and count for quick debugging."""
    hashes = cache_utils.list_cache_files()
    return success_response({
        "cached_count": len(hashes),
        "cached_hashes": hashes
    })


@router.get(
    "/quality-score/{resume_hash}",
    response_model=SuccessResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_quality_score(resume_hash: str):
    """
    Get the quality score for an already-parsed resume using its hash.
    Loads from cache so no LLM call needed.
    
    Parameters:
        resume_hash: The hash of the resume to get quality score for
        
    Returns:
        Success response with quality score breakdown, grade, and suggestions
    """
    try:
        from utils.quality_score import calculate_resume_quality
        
        # Load cached data
        cached = cache_utils.load_from_cache(resume_hash)
        if not cached:
            return error_response(
                "No cached data found for this resume hash",
                detail="Upload the resume first using /resume/parse-preview",
                status_code=404
            )
        
        # Check if quality already in cached data
        if "quality" in cached:
            return success_response(cached["quality"])
        
        # If quality not in cached data (older cache), recalculate it
        if "parsed" in cached:
            quality = calculate_resume_quality(cached["parsed"])
            return success_response(quality)
        
        # If no parsed data either, this cache is incomplete
        return error_response(
            "Cached data is incomplete",
            detail="Please re-upload the resume",
            status_code=400
        )
        
    except Exception as e:
        logger.error(f"Error getting quality score: {e}")
        return error_response("Internal server error", detail=str(e), status_code=500)


# ═══════════════════════════════════════════════════════════════════════════
# BULK UPLOAD ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.post(
    "/bulk-upload",
    response_model=SuccessResponse,
    responses={400: {"model": ErrorResponse}, 413: {"model": ErrorResponse}}
)
async def bulk_upload_resumes(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload multiple resumes (max 10) for batch processing.
    Returns batch_id immediately. Processing happens in background.
    Check /resume/bulk-status/{batch_id} for progress.
    """
    from utils.bulk_tracker import create_batch
    
    try:
        # Validate file count
        if len(files) == 0:
            return error_response("No files provided", status_code=400)
        
        if len(files) > 10:
            return error_response(
                "Maximum 10 files allowed per batch",
                detail=f"You provided {len(files)} files",
                status_code=400
            )
        
        # Validate each file extension
        allowed = [".pdf", ".docx"]
        filenames = []
        files_data = []
        
        for file in files:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in allowed:
                return error_response(
                    f"Unsupported file type: {file.filename}",
                    detail="Only PDF and DOCX files are supported",
                    status_code=400
                )
            
            # Read file bytes
            file_bytes = await file.read()
            
            # Validate file size
            max_bytes = settings.max_file_size_mb * 1024 * 1024
            if len(file_bytes) > max_bytes:
                return error_response(
                    f"File too large: {file.filename}",
                    detail=f"Max size is {settings.max_file_size_mb}MB",
                    status_code=413
                )
            
            filenames.append(file.filename)
            files_data.append({
                "filename": file.filename,
                "file_bytes": file_bytes,
                "extension": ext
            })
        
        # Create batch ID and tracker
        batch_id = str(uuid.uuid4())
        batch = create_batch(batch_id, filenames)
        
        logger.info(f"[BULK] Created batch: {batch_id[:8]}...")
        logger.info(f"[BULK] Files: {filenames}")
        print(f"[BULK] Created batch: {batch_id[:8]}...")
        print(f"[BULK] Files: {filenames}")
        
        # Start background processing
        background_tasks.add_task(
            orchestrator_service.process_bulk_resumes,
            batch_id,
            files_data
        )
        
        return success_response({
            "batch_id": batch_id,
            "message": f"Batch created. Processing {len(files)} files in background.",
            "total_files": len(files),
            "filenames": filenames,
            "status_url": f"/resume/bulk-status/{batch_id}",
            "note": "Processing takes 10-15 seconds per file. Check status_url for progress."
        }, status_code=202)
        
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        logger.error(f"Unexpected error in /resume/bulk-upload: {e}")
        return error_response("Internal server error", detail=str(e), status_code=500)


@router.get(
    "/bulk-status/{batch_id}",
    response_model=SuccessResponse,
    responses={404: {"model": ErrorResponse}}
)
async def get_bulk_status(batch_id: str):
    """
    Get the current processing status of a bulk upload batch.
    Poll this endpoint every 10 seconds to track progress.
    
    Parameters:
        batch_id: The batch ID returned from /resume/bulk-upload
        
    Returns:
        Success response with batch status, file list, and progress percentage
    """
    from utils.bulk_tracker import load_batch
    
    try:
        batch = load_batch(batch_id)
        
        if not batch:
            return error_response(
                "Batch not found",
                detail=f"No batch found with ID: {batch_id}",
                status_code=404
            )
        
        # Calculate progress percentage
        done = batch["completed"] + batch["failed"]
        total = batch["total_files"]
        progress_pct = round((done / total) * 100) if total > 0 else 0
        
        logger.info(f"[BULK STATUS] Batch {batch_id[:8]}...")
        logger.info(f"[BULK STATUS] Progress: {done}/{total} ({progress_pct}%)")
        print(f"[BULK STATUS] Batch {batch_id[:8]}...")
        print(f"[BULK STATUS] Progress: {done}/{total} ({progress_pct}%)")
        
        return success_response({
            "batch_id": batch_id,
            "status": batch["status"],
            "progress_percent": progress_pct,
            "total_files": total,
            "completed": batch["completed"],
            "failed": batch["failed"],
            "pending": total - done,
            "created_at": batch["created_at"],
            "finished_at": batch.get("finished_at"),
            "files": batch["files"]
        })
        
    except Exception as e:
        logger.error(f"Error getting bulk status: {e}")
        return error_response("Internal server error", detail=str(e), status_code=500)
