from pydantic import BaseModel
from typing import Optional


class SaveAddressRequest(BaseModel):
    student_id: int
    address_line_1: str
    address_line_2: Optional[str] = None
    care_of: Optional[str] = None
    landmark: Optional[str] = None
    pincode_id: int                        # already resolved pincode_id, not raw string
    address_type: Optional[str] = "current"


class SaveAddressResponse(BaseModel):
    address_id: int
