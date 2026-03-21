from sqlalchemy import Column, Integer, String, VARCHAR, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class StudentProject(Base):
    """tbl_cp_studentprojects - Student project records."""
    __tablename__ = "tbl_cp_studentprojects"

    row_id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, nullable=False, unique=True)
    student_id = Column(Integer, nullable=False)
    workexp_id = Column(Integer, nullable=True)
    project_title = Column(VARCHAR(255), nullable=False)
    project_description = Column(Text, nullable=True)
    achievements = Column(Text, nullable=True)
    project_start_date = Column(String, default='1900-01-01')
    project_end_date = Column(String, default='1900-01-01')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
