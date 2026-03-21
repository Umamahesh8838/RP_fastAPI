from pydantic import BaseModel
from typing import Optional


class SaveStudentRequest(BaseModel):
    salutation_id: Optional[int] = None
    first_name: str
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    email: str
    alt_email: Optional[str] = None
    contact_number: Optional[str] = None
    alt_contact_number: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    date_of_birth: Optional[str] = None    # YYYY-MM-DD
    current_city: Optional[str] = None
    gender: Optional[str] = None


class SaveStudentResponse(BaseModel):
    student_id: int
    already_exists: bool
