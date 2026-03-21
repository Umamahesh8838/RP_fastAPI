from pydantic import BaseModel
from typing import Optional


class SaveProjectRequest(BaseModel):
    student_id: int
    workexp_id: Optional[int] = None
    project_title: str
    project_description: Optional[str] = None
    achievements: Optional[str] = None
    project_start_date: Optional[str] = None   # YYYY-MM-DD
    project_end_date: Optional[str] = None     # YYYY-MM-DD


class SaveProjectResponse(BaseModel):
    project_id: int


class SaveProjectSkillRequest(BaseModel):
    project_id: int
    skill_id: int


class SaveProjectSkillResponse(BaseModel):
    already_exists: bool
