from pydantic import BaseModel
from typing import Any, Optional


class SuccessResponse(BaseModel):
    """Standard success response wrapper for all endpoints."""
    success: bool = True
    data: Any


class ErrorResponse(BaseModel):
    """Standard error response wrapper for all endpoints."""
    success: bool = False
    error: str
    detail: Optional[str] = None
