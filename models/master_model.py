from sqlalchemy import Column, Integer, String, VARCHAR, DateTime, Text, Boolean, Numeric, DECIMAL, ForeignKey, DATETIME
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class MasterSalutation(Base):
    """tbl_cp_msalutation - Master table for salutations."""
    __tablename__ = "tbl_cp_msalutation"

    row_id = Column(Integer, primary_key=True, autoincrement=True)
    salutation_id = Column(Integer, nullable=False, unique=True)
    value = Column(VARCHAR(50), nullable=False, unique=True)
    description = Column(VARCHAR(255), default='No description')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MasterLanguage(Base):
    """tbl_cp_mlanguages - Master table for languages."""
    __tablename__ = "tbl_cp_mlanguages"

    row_id = Column(Integer, primary_key=True, autoincrement=True)
    language_id = Column(Integer, nullable=False, unique=True)
    language_code = Column(VARCHAR(20), nullable=False, unique=True)
    language_name = Column(VARCHAR(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MasterInterest(Base):
    """tbl_cp_minterests - Master table for interests."""
    __tablename__ = "tbl_cp_minterests"

    row_id = Column(Integer, primary_key=True, autoincrement=True)
    interest_id = Column(Integer, nullable=False, unique=True)
    name = Column(VARCHAR(150), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MasterCourse(Base):
    """tbl_cp_mcourses - Master table for courses."""
    __tablename__ = "tbl_cp_mcourses"

    row_id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, nullable=False, unique=True)
    course_name = Column(VARCHAR(150), nullable=False)
    course_code = Column(VARCHAR(50), nullable=False)
    specialization_name = Column(VARCHAR(150), nullable=False, default='General')
    specialization_code = Column(VARCHAR(50), nullable=False, default='GEN')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MasterCollege(Base):
    """tbl_cp_mcolleges - Master table for colleges."""
    __tablename__ = "tbl_cp_mcolleges"

    row_id = Column(Integer, primary_key=True, autoincrement=True)
    college_id = Column(Integer, nullable=False, unique=True)
    college_name = Column(VARCHAR(255), nullable=False, unique=True)
    spoc_name = Column(VARCHAR(150), default='Not Assigned')
    spoc_phone = Column(VARCHAR(20), default='0000000000')
    spoc_email = Column(VARCHAR(255), default='noreply@college.com')
    tpo_name = Column(VARCHAR(150), default='Not Assigned')
    tpo_phone = Column(VARCHAR(20), default='0000000000')
    tpo_email = Column(VARCHAR(255), default='noreply@college.com')
    student_coordinator_name = Column(VARCHAR(150), default='Not Assigned')
    student_coordinator_phone = Column(VARCHAR(20), default='0000000000')
    student_coordinator_email = Column(VARCHAR(255), default='noreply@college.com')
    reference_details = Column(Text, nullable=True)
    priority = Column(Integer, nullable=False, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MasterCertification(Base):
    """tbl_cp_mcertifications - Master table for certifications."""
    __tablename__ = "tbl_cp_mcertifications"

    row_id = Column(Integer, primary_key=True, autoincrement=True)
    certification_id = Column(Integer, nullable=False, unique=True)
    certification_name = Column(VARCHAR(255), nullable=False)
    certification_code = Column(VARCHAR(100), nullable=False, unique=True)
    issuing_organization = Column(VARCHAR(255), nullable=False)
    certification_type = Column(VARCHAR(100), default='General')
    mode = Column(VARCHAR(50), default='Online')
    validity_period_value = Column(Integer, default=0)
    validity_period_unit = Column(VARCHAR(20), default='Years')
    is_lifetime = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MasterSkill(Base):
    """tbl_cp_mskills - Master table for skills."""
    __tablename__ = "tbl_cp_mskills"

    row_id = Column(Integer, primary_key=True, autoincrement=True)
    skill_id = Column(Integer, nullable=False, unique=True)
    name = Column(VARCHAR(100), nullable=False, unique=True)
    description = Column(VARCHAR(255), default='No description')
    language_id = Column(Integer, nullable=False)
    version = Column(VARCHAR(50), default='N/A')
    complexity = Column(VARCHAR(50), default='Beginner')
    status = Column(VARCHAR(30), default='Active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MasterCountry(Base):
    """tbl_cp_mcountries - Master table for countries."""
    __tablename__ = "tbl_cp_mcountries"

    row_id = Column(Integer, primary_key=True, autoincrement=True)
    country_id = Column(Integer, nullable=False, unique=True)
    country_name = Column(VARCHAR(100), nullable=False, unique=True)
    country_code = Column(VARCHAR(5), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MasterState(Base):
    """tbl_cp_mstates - Master table for states."""
    __tablename__ = "tbl_cp_mstates"

    row_id = Column(Integer, primary_key=True, autoincrement=True)
    state_id = Column(Integer, nullable=False, unique=True)
    state_name = Column(VARCHAR(100), nullable=False)
    state_code = Column(VARCHAR(10), default='XX')
    country_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MasterCity(Base):
    """tbl_cp_mcities - Master table for cities."""
    __tablename__ = "tbl_cp_mcities"

    row_id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(Integer, nullable=False, unique=True)
    city_name = Column(VARCHAR(100), nullable=False)
    state_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MasterPincode(Base):
    """tbl_cp_mpincodes - Master table for pincodes."""
    __tablename__ = "tbl_cp_mpincodes"

    row_id = Column(Integer, primary_key=True, autoincrement=True)
    pincode_id = Column(Integer, nullable=False, unique=True)
    pincode = Column(VARCHAR(20), nullable=False, unique=True)
    city_id = Column(Integer, nullable=False)
    area_name = Column(VARCHAR(150), default='Unknown Area')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ResumeHash(Base):
    """tbl_cp_resume_hashes - Stores SHA-256 hashes of processed resumes."""
    __tablename__ = "tbl_cp_resume_hashes"

    hash = Column(VARCHAR(64), primary_key=True)
    student_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
