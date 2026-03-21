from sqlalchemy import Column, Integer, String, VARCHAR, DateTime, Text, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class StudentWorkExp(Base):
    """tbl_cp_student_workexp - Work experience records."""
    __tablename__ = "tbl_cp_student_workexp"

    row_id = Column(Integer, primary_key=True, autoincrement=True)
    workexp_id = Column(Integer, nullable=False, unique=True)
    student_id = Column(Integer, nullable=False)
    company_name = Column(VARCHAR(255), nullable=False)
    company_location = Column(VARCHAR(150), default='Not Specified')
    designation = Column(VARCHAR(150), default='Not Specified')
    employment_type = Column(VARCHAR(50), default='Full-Time')
    start_date = Column(String, nullable=False, default='1900-01-01')
    end_date = Column(String, default='1900-01-01')
    is_current = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
