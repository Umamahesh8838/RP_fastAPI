from pydantic import BaseModel, field_validator
from typing import Optional, List


class SchoolItem(BaseModel):
    """One school education entry extracted from resume."""
    standard: Optional[str] = None           # "10th" or "12th"
    board: Optional[str] = None              # "CBSE", "ICSE", "Maharashtra State Board"
    school_name: Optional[str] = None
    percentage: Optional[float] = None       # decimal e.g. 85.60
    passing_year: Optional[int] = None       # e.g. 2018

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


class EducationItem(BaseModel):
    """One college/university education entry extracted from resume."""
    college_name: Optional[str] = None       # full institution name
    course_name: Optional[str] = None        # "Bachelor of Technology"
    specialization_name: Optional[str] = None  # "Computer Science"
    start_year: Optional[int] = None
    end_year: Optional[int] = None           # null if currently studying
    cgpa: Optional[float] = None
    percentage: Optional[float] = None       # fill only if explicitly stated

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


class WorkExpItem(BaseModel):
    """One work experience entry extracted from resume."""
    company_name: Optional[str] = None
    company_location: Optional[str] = None   # city or city+country
    designation: Optional[str] = None        # exact job title as written
    employment_type: Optional[str] = None    # "Full-Time","Part-Time","Internship","Freelance","Contract"
    start_date: Optional[str] = None         # YYYY-MM-DD
    end_date: Optional[str] = None           # YYYY-MM-DD or null if is_current
    is_current: Optional[bool] = None


class ProjectItem(BaseModel):
    """One project entry extracted from resume."""
    project_title: Optional[str] = None
    project_description: Optional[str] = None
    achievements: Optional[str] = None       # outcomes/results/impact
    project_start_date: Optional[str] = None # YYYY-MM-DD
    project_end_date: Optional[str] = None   # YYYY-MM-DD
    workexp_company_name: Optional[str] = None  # company name if project was done at an employer
    skills_used: List[str] = []              # list of skill name strings used in this project


class SkillItem(BaseModel):
    """One skill entry extracted from resume."""
    name: Optional[str] = None
    complexity: Optional[str] = None         # "Beginner", "Intermediate", "Expert"


class LanguageItem(BaseModel):
    """One spoken/written language entry extracted from resume."""
    language_name: Optional[str] = None      # "English", "Hindi", "Tamil"


class CertificationItem(BaseModel):
    """One certification entry extracted from resume."""
    certification_name: Optional[str] = None
    issuing_organization: Optional[str] = None  # "Coursera", "Amazon Web Services"
    certification_type: Optional[str] = None    # "Cloud", "Data Science"
    issue_date: Optional[str] = None            # YYYY-MM-DD
    expiry_date: Optional[str] = None           # YYYY-MM-DD
    is_lifetime: Optional[bool] = None          # true if no expiry mentioned
    certificate_url: Optional[str] = None
    credential_id: Optional[str] = None


class InterestItem(BaseModel):
    """
    One domain/area interest extracted from resume.
    This is NOT hobbies. This is career domain interest like:
    "Machine Learning", "Web Development", "Cybersecurity", "Data Science", "Cloud Computing"
    """
    name: Optional[str] = None
    is_inferred: Optional[bool] = None   # true if inferred from profile, false if explicitly stated


class AddressItem(BaseModel):
    """One address entry extracted from resume."""
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    landmark: Optional[str] = None
    pincode: Optional[str] = None        # raw pincode string — will be looked up later
    city_name: Optional[str] = None
    state_name: Optional[str] = None
    country_name: Optional[str] = None
    address_type: Optional[str] = None  # "current" or "permanent"


class ParsedResume(BaseModel):
    """
    Complete structured data extracted from a resume by the LLM.
    Every field name matches exactly the corresponding DB column name.
    """
    # tbl_cp_student fields
    salutation: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    alt_email: Optional[str] = None
    contact_number: Optional[str] = None
    alt_contact_number: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    date_of_birth: Optional[str] = None  # YYYY-MM-DD
    current_city: Optional[str] = None
    gender: Optional[str] = None

    # Related tables
    school: List[SchoolItem] = []
    education: List[EducationItem] = []
    workexp: List[WorkExpItem] = []
    projects: List[ProjectItem] = []
    skills: List[SkillItem] = []
    languages: List[LanguageItem] = []
    certifications: List[CertificationItem] = []
    interests: List[InterestItem] = []
    addresses: List[AddressItem] = []


class ParseResumeRequest(BaseModel):
    """Request body for /parse/resume endpoint."""
    resume_text: str   # minimum 100 characters


class ParseResumeResponse(BaseModel):
    """Response from /parse/resume endpoint."""
    parsed: ParsedResume
    resume_hash: str   # SHA-256 hash of resume_text


class SaveConfirmedRequest(BaseModel):
    """
    Request body for /resume/save-confirmed endpoint.
    Contains the confirmed/edited ParsedResume and resume hash.
    """
    resume_hash: str
    parsed: ParsedResume