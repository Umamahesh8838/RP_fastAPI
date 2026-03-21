import hashlib


def compute_resume_hash(resume_text: str) -> str:
    """
    Computes SHA-256 hash of resume text for duplicate detection.
    Text is stripped and encoded to UTF-8 before hashing.
    Returns 64-character hex string.
    """
    return hashlib.sha256(resume_text.strip().encode("utf-8")).hexdigest()
