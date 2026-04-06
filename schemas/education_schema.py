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

    @field_validator('start_year', 'end_year', mode='before')
    @classmethod
    def clean_years(cls, v):
        # None is OK
        if v is None:
            return None
        # Already an integer
        if isinstance(v, int):
            return v
        # String - extract year
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return None
            # Try to extract first 4-digit year (handles "2026-01-01" or "2026")
            import re
            m = re.search(r'(\d{4})', v)
            if m:
                try:
                    return int(m.group(1))
                except (ValueError, TypeError):
                    return None
            # Fallback: try direct int conversion
            try:
                return int(v)
            except (ValueError, TypeError):
                return None
        # For other types, convert to string and try
        try:
            s = str(v).strip()
            import re
            m = re.search(r'(\d{4})', s)
            if m:
                return int(m.group(1))
            return int(s)
        except (ValueError, TypeError, AttributeError):
            return None

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
