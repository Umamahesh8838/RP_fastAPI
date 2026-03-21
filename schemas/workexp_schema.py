from pydantic import BaseModel
from typing import Optional


class SaveWorkExpRequest(BaseModel):
    student_id: int
    company_name: str
    company_location: Optional[str] = None
    designation: Optional[str] = None
    employment_type: Optional[str] = None
    start_date: Optional[str] = None       # YYYY-MM-DD
    end_date: Optional[str] = None         # YYYY-MM-DD — set to None if is_current=True
    is_current: Optional[bool] = None


class SaveWorkExpResponse(BaseModel):
    workexp_id: int
