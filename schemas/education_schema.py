from pydantic import BaseModel, field_validator
from typing import Optional


class SaveSchoolRequest(BaseModel):
    student_id: int
    standard: str                          # "10th" or "12th"
    board: Optional[str] = None
    school_name: Optional[str] = None
    percentage: Optional[float] = None
    passing_year: Optional[int] = None

    @field_validator('percentage', mode='before')
    @classmethod
    def clean_percentage(cls, v):
        if isinstance(v, str):
            v = v.replace('%', '').strip()
            if not v:
                return None
            try:
                return float(v)
            except ValueError:
                return None
        return v


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

    @field_validator('cgpa', 'percentage', mode='before')
    @classmethod
    def clean_floats(cls, v):
        if isinstance(v, str):
            v = v.replace('%', '').strip()
            if not v:
                return None
            try:
                return float(v)
            except ValueError:
                return None
        return v


class SaveEducationResponse(BaseModel):
    edu_id: int
