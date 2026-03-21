from pydantic import BaseModel
from typing import Optional


class LookupSkillRequest(BaseModel):
    name: str
    complexity: Optional[str] = "Intermediate"


class LookupSkillResponse(BaseModel):
    skill_id: int
    name: str
    complexity: str
    is_new: bool


class LookupLanguageRequest(BaseModel):
    language_name: str


class LookupLanguageResponse(BaseModel):
    language_id: int
    language_name: str
    language_code: str
    is_new: bool


class LookupInterestRequest(BaseModel):
    name: str


class LookupInterestResponse(BaseModel):
    interest_id: int
    name: str
    is_new: bool


class LookupCertificationRequest(BaseModel):
    certification_name: str
    issuing_organization: str
    certification_type: Optional[str] = "General"
    is_lifetime: Optional[bool] = None


class LookupCertificationResponse(BaseModel):
    certification_id: int
    certification_name: str
    certification_code: str
    issuing_organization: str
    is_new: bool


class LookupCollegeRequest(BaseModel):
    college_name: str


class LookupCollegeResponse(BaseModel):
    college_id: int
    college_name: str
    is_new: bool


class LookupCourseRequest(BaseModel):
    course_name: str
    specialization_name: Optional[str] = "General"


class LookupCourseResponse(BaseModel):
    course_id: int
    course_name: str
    course_code: str
    specialization_name: str
    specialization_code: str
    is_new: bool


class LookupSalutationRequest(BaseModel):
    value: str


class LookupSalutationResponse(BaseModel):
    salutation_id: Optional[int]
    value: str
    found: bool


class LookupPincodeRequest(BaseModel):
    pincode: str


class LookupPincodeResponse(BaseModel):
    pincode_id: Optional[int]
    pincode: str
    found: bool
