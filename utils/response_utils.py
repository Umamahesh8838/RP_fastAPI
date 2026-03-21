from fastapi.responses import JSONResponse
from typing import Any, Optional


def success_response(data: Any, status_code: int = 200) -> JSONResponse:
    """Returns standard success JSON response."""
    return JSONResponse(
        status_code=status_code,
        content={"success": True, "data": data}
    )


def error_response(error: str, detail: Optional[str] = None, status_code: int = 400) -> JSONResponse:
    """Returns standard error JSON response."""
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "error": error, "detail": detail}
    )
