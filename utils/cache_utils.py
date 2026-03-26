import json
import os
import logging
from datetime import datetime

CACHE_DIR = "resume_cache"
logger = logging.getLogger(__name__)

def ensure_cache_dir():
    """Creates the resume_cache folder if it does not exist."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
        logger.info(f"Created cache directory: {CACHE_DIR}")

def save_to_cache(resume_hash: str, data: dict) -> str:
    """
    Saves parsed resume data to a JSON file in resume_cache folder.
    Also writes a metadata file with quick lookup details.
    Returns the file path where data was saved.
    """
    ensure_cache_dir()
    file_path = os.path.join(CACHE_DIR, f"{resume_hash}.json")
    meta_path = os.path.join(CACHE_DIR, f"{resume_hash}_meta.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    parsed = data.get("parsed", {}) if isinstance(data, dict) else {}
    first_name = parsed.get("first_name") or ""
    last_name = parsed.get("last_name") or ""
    email = parsed.get("email") or ""
    meta = {
        "saved_at": datetime.utcnow().isoformat(),
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
    }
    with open(meta_path, "w", encoding="utf-8") as mf:
        json.dump(meta, mf, indent=2, ensure_ascii=False)

    logger.info(f"[CACHE SAVE] Saved resume for {first_name} {last_name} - hash: {resume_hash[:8]}...")
    return file_path

def load_from_cache(resume_hash: str) -> dict | None:
    """
    Loads parsed resume data from cache file by resume_hash.
    Returns the parsed dict if found, None if not found.
    """
    ensure_cache_dir()
    file_path = os.path.join(CACHE_DIR, f"{resume_hash}.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"[CACHE HIT] Found cached data for hash: {resume_hash[:8]}...")
        return data
    logger.info(f"[CACHE MISS] No cache for hash: {resume_hash[:8]}...")
    return None


def check_hash_exists(resume_hash: str) -> bool:
    """Returns True if cache file exists for this hash."""
    ensure_cache_dir()
    file_path = os.path.join(CACHE_DIR, f"{resume_hash}.json")
    return os.path.exists(file_path)

def delete_from_cache(resume_hash: str):
    """
    Deletes cache file after data has been saved to database.
    Cleans up temp files after successful save-confirmed.
    """
    ensure_cache_dir()
    file_path = os.path.join(CACHE_DIR, f"{resume_hash}.json")
    meta_path = os.path.join(CACHE_DIR, f"{resume_hash}_meta.json")
    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"[CACHE] Deleted cache file: {file_path}")
    if os.path.exists(meta_path):
        os.remove(meta_path)
        logger.info(f"[CACHE] Deleted cache metadata: {meta_path}")

def list_cache_files() -> list:
    """Returns list of all cached resume hashes."""
    ensure_cache_dir()
    files = os.listdir(CACHE_DIR)
    hashes = [
        f.replace(".json", "")
        for f in files
        if f.endswith(".json") and not f.endswith("_meta.json")
    ]
    logger.info(f"[CACHE] Currently cached resumes: {len(hashes)}")
    return hashes
