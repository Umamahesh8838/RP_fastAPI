from sqlalchemy import Column, Integer, String, VARCHAR, DateTime, Text, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class M2MStudentSkill(Base):
    """tbl_cp_m2m_std_skill - Many-to-many relationship between students and skills."""
    __tablename__ = "tbl_cp_m2m_std_skill"

    row_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, nullable=False)
    skill_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class M2MStudentLanguage(Base):
    """tbl_cp_m2m_std_lng - Many-to-many relationship between students and languages."""
    __tablename__ = "tbl_cp_m2m_std_lng"

    row_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, nullable=False)
    language_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class M2MStudentInterest(Base):
    """tbl_cp_m2m_std_interest - Many-to-many relationship between students and interests."""
    __tablename__ = "tbl_cp_m2m_std_interest"

    row_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, nullable=False)
    interest_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class M2MStudentCertification(Base):
    """tbl_cp_m2m_student_certification - Many-to-many relationship between students and certifications."""
    __tablename__ = "tbl_cp_m2m_student_certification"

    row_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, nullable=False)
    certification_id = Column(Integer, nullable=False)
    issue_date = Column(String, default='1900-01-01')
    expiry_date = Column(String, default='9999-12-31')
    certificate_url = Column(VARCHAR(500), default='')
    credential_id = Column(VARCHAR(150), default='')
    is_verified = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class M2MProjectSkill(Base):
    """tbl_cp_m2m_studentproject_skill - Many-to-many relationship between projects and skills."""
    __tablename__ = "tbl_cp_m2m_studentproject_skill"

    row_id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, nullable=False)
    skill_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
