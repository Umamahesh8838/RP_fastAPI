from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List
import re


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

    @model_validator(mode='before')
    @classmethod
    def normalize_years_payload(cls, data):
        """Normalize year-like values before field-level parsing."""
        if not isinstance(data, dict):
            return data

        for year_field in ['start_year', 'end_year']:
            val = data.get(year_field)
            if val is None or isinstance(val, int):
                continue

            if isinstance(val, str):
                s = val.strip()
                if not s:
                    data[year_field] = None
                    continue
                m = re.search(r'(\d{4})', s)
                if m:
                    try:
                        data[year_field] = int(m.group(1))
                        continue
                    except (ValueError, TypeError):
                        data[year_field] = None
                        continue
                try:
                    data[year_field] = int(s)
                except (ValueError, TypeError):
                    data[year_field] = None
                continue

            try:
                s = str(val).strip()
                m = re.search(r'(\d{4})', s)
                data[year_field] = int(m.group(1)) if m else int(s)
            except (ValueError, TypeError, AttributeError):
                data[year_field] = None

        return data

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

    @field_validator('education', mode='before')
    @classmethod
    def normalize_education_before(cls, v):
        """Pre-process education list to ensure years are integers before nested model validation."""
        if not isinstance(v, list):
            return v
        
        for edu in v:
            if not isinstance(edu, dict):
                continue
            
            for year_field in ['start_year', 'end_year']:
                val = edu.get(year_field)
                if val is None:
                    continue
                if isinstance(val, int):
                    continue
                if isinstance(val, str):
                    s = val.strip()
                    if not s:
                        edu[year_field] = None
                        continue
                    m = re.search(r'(\d{4})', s)
                    if m:
                        try:
                            edu[year_field] = int(m.group(1))
                        except (ValueError, TypeError):
                            edu[year_field] = None
                    else:
                        try:
                            edu[year_field] = int(s)
                        except (ValueError, TypeError):
                            edu[year_field] = None
                else:
                    try:
                        s = str(val).strip()
                        m = re.search(r'(\d{4})', s)
                        edu[year_field] = int(m.group(1)) if m else int(s)
                    except (ValueError, TypeError, AttributeError):
                        edu[year_field] = None
        return v

    @model_validator(mode='after')
    def normalize_education_after(self):
        """Extra safety: ensure education years are always integers after model construction."""
        for edu in self.education:
            for year_field in ['start_year', 'end_year']:
                val = getattr(edu, year_field, None)
                if val is not None and not isinstance(val, int):
                    if isinstance(val, str):
                        m = re.search(r'(\d{4})', val)
                        if m:
                            try:
                                setattr(edu, year_field, int(m.group(1)))
                            except (ValueError, TypeError):
                                setattr(edu, year_field, None)
        return self

    @model_validator(mode='before')
    @classmethod
    def normalize_lists_before_validation(cls, data):
        """Convert string items in lists to proper objects before Pydantic validation."""
        if not isinstance(data, dict):
            return data
        
        # Convert string->InterestItem
        if 'interests' in data and isinstance(data['interests'], list):
            normalized = []
            for item in data['interests']:
                if isinstance(item, str):
                    normalized.append({"name": item, "is_inferred": False})
                else:
                    normalized.append(item)
            data['interests'] = normalized
        
        # Convert string->SkillItem
        if 'skills' in data and isinstance(data['skills'], list):
            normalized = []
            for item in data['skills']:
                if isinstance(item, str):
                    normalized.append({"name": item, "complexity": None})
                else:
                    normalized.append(item)
            data['skills'] = normalized
        
        # Convert string->LanguageItem
        if 'languages' in data and isinstance(data['languages'], list):
            normalized = []
            for item in data['languages']:
                if isinstance(item, str):
                    normalized.append({"language_name": item})
                else:
                    normalized.append(item)
            data['languages'] = normalized
        
        # Convert string->CertificationItem
        if 'certifications' in data and isinstance(data['certifications'], list):
            normalized = []
            for item in data['certifications']:
                if isinstance(item, str):
                    normalized.append({"certification_name": item})
                else:
                    normalized.append(item)
            data['certifications'] = normalized
        
        return data


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