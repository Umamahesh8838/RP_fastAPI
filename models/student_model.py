from sqlalchemy import Column, Integer, String, VARCHAR, DateTime, Text, Boolean, Numeric, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class Student(Base):
    """tbl_cp_student - Student records."""
    __tablename__ = "tbl_cp_student"

    row_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, nullable=False, unique=True)
    salutation_id = Column(Integer, nullable=True)
    first_name = Column(VARCHAR(100), nullable=False)
    middle_name = Column(VARCHAR(100), default='')
    last_name = Column(VARCHAR(100), default='')
    email = Column(VARCHAR(255), nullable=False, unique=True)
    alt_email = Column(VARCHAR(255), default='')
    contact_number = Column(VARCHAR(20), unique=True, nullable=True)
    alt_contact_number = Column(VARCHAR(20), default='0000000000')
    linkedin_url = Column(VARCHAR(255), default='')
    github_url = Column(VARCHAR(255), default='')
    portfolio_url = Column(VARCHAR(255), default='')
    resume_url = Column(VARCHAR(500), default='')
    profile_photo_url = Column(VARCHAR(500), nullable=False, default='default_profile.png')
    date_of_birth = Column(String, nullable=False, default='1900-01-01')
    current_city = Column(VARCHAR(100), default='Not Specified')
    gender = Column(VARCHAR(20), default='Not Specified')
    user_type = Column(VARCHAR(100), default='Student')
    is_active = Column(Boolean, nullable=True)
    status = Column(VARCHAR(30), nullable=False, default='Active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
