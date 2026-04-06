"""Bulk upload batch tracking system using JSON files."""

import json
import os
import logging
from datetime import datetime

BULK_CACHE_DIR = "resume_cache/bulk"
logger = logging.getLogger(__name__)


def ensure_bulk_dir():
    """Creates resume_cache/bulk folder if not exists."""
    os.makedirs(BULK_CACHE_DIR, exist_ok=True)
    logger.info(f"Bulk cache directory ensured: {BULK_CACHE_DIR}")


def create_batch(batch_id: str, filenames: list) -> dict:
    """
    Creates a new batch tracking record.
    
    Parameters:
        batch_id: unique ID for this batch
        filenames: list of uploaded filenames
        
    Returns:
        The created batch record dict
    """
    ensure_bulk_dir()
    
    batch = {
        "batch_id": batch_id,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_files": len(filenames),
        "completed": 0,
        "failed": 0,
        "status": "processing",
        "files": [
            {
                "filename": name,
                "status": "pending",
                "resume_hash": None,
                "student_name": None,
                "email": None,
                "quality_score": None,
                "error": None,
                "started_at": None,
                "completed_at": None
            }
            for name in filenames
        ]
    }
    
    save_batch(batch_id, batch)
    logger.info(f"[BULK] Created batch {batch_id[:8]}... with {len(filenames)} files")
    return batch


def save_batch(batch_id: str, batch: dict):
    """Saves batch status to JSON file."""
    ensure_bulk_dir()
    path = os.path.join(BULK_CACHE_DIR, f"{batch_id}.json")
    with open(path, "w") as f:
        json.dump(batch, f, indent=2)


def load_batch(batch_id: str) -> dict | None:
    """Loads batch status from JSON file."""
    path = os.path.join(BULK_CACHE_DIR, f"{batch_id}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None


def update_file_status(
    batch_id: str,
    filename: str,
    status: str,
    resume_hash: str = None,
    student_name: str = None,
    email: str = None,
    quality_score: int = None,
    error: str = None
):
    """
    Updates the status of one file inside a batch.
    
    status values:
      pending    → not started yet
      processing → currently being parsed
      complete   → successfully parsed
      failed     → error occurred
    """
    batch = load_batch(batch_id)
    if not batch:
        logger.warning(f"[BULK] Batch {batch_id[:8]}... not found for status update")
        return
    
    for file_record in batch["files"]:
        if file_record["filename"] == filename:
            file_record["status"] = status
            if resume_hash:
                file_record["resume_hash"] = resume_hash
            if student_name:
                file_record["student_name"] = student_name
            if email:
                file_record["email"] = email
            if quality_score is not None:
                file_record["quality_score"] = quality_score
            if error:
                file_record["error"] = error
            if status == "processing":
                file_record["started_at"] = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            if status in ("complete", "failed"):
                file_record["completed_at"] = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
    
    # Update batch summary counts
    completed = sum(
        1 for f in batch["files"] if f["status"] == "complete"
    )
    failed = sum(
        1 for f in batch["files"] if f["status"] == "failed"
    )
    batch["completed"] = completed
    batch["failed"] = failed
    
    # Check if entire batch is done
    done = completed + failed
    if done == batch["total_files"]:
        batch["status"] = "complete"
        batch["finished_at"] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        logger.info(f"[BULK] Batch {batch_id[:8]}... complete!")
        logger.info(f"[BULK] Success: {completed} | Failed: {failed}")
    
    save_batch(batch_id, batch)


def list_batches() -> list:
    """Returns list of all batch IDs."""
    ensure_bulk_dir()
    if not os.path.exists(BULK_CACHE_DIR):
        return []
    files = os.listdir(BULK_CACHE_DIR)
    return [f.replace(".json", "") for f in files 
            if f.endswith(".json")]
