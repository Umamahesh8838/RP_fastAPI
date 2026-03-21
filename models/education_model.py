from sqlalchemy import Column, Integer, String, VARCHAR, DateTime, Text, Boolean, Numeric, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class StudentSchool(Base):
    """tbl_cp_student_school - School education records."""
    __tablename__ = "tbl_cp_student_school"

    row_id = Column(Integer, primary_key=True, autoincrement=True)
    school_id = Column(Integer, nullable=False, unique=True)
    student_id = Column(Integer, nullable=False)
    standard = Column(VARCHAR(50), nullable=False)
    board = Column(VARCHAR(100), default='Not Specified')
    school_name = Column(VARCHAR(255), default='Not Specified')
    percentage = Column(DECIMAL(5, 2), nullable=False, default=0.00)
    passing_year = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StudentEducation(Base):
    """tbl_cp_student_education - College/University education records."""
    __tablename__ = "tbl_cp_student_education"

    row_id = Column(Integer, primary_key=True, autoincrement=True)
    edu_id = Column(Integer, nullable=False, unique=True)
    student_id = Column(Integer, nullable=False)
    college_id = Column(Integer, nullable=False)
    course_id = Column(Integer, nullable=False)
    start_year = Column(Integer, default=0)
    end_year = Column(Integer, default=0)
    cgpa = Column(DECIMAL(4, 2), default=0.00)
    percentage = Column(DECIMAL(5, 2), default=0.00)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
