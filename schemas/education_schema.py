from pydantic import BaseModel
from typing import Optional


class SaveSchoolRequest(BaseModel):
    student_id: int
    standard: str                          # "10th" or "12th"
    board: Optional[str] = None
    school_name: Optional[str] = None
    percentage: Optional[float] = None
    passing_year: Optional[int] = None


class SaveSchoolResponse(BaseModel):
    school_id: int


class SaveEducationRequest(BaseModel):
    student_id: int
    college_id: int
    course_id: int
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    cgpa: Optional[float] = None
    percentage: Optional[float] = None


class SaveEducationResponse(BaseModel):
    edu_id: int
