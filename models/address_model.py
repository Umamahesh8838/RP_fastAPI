from sqlalchemy import Column, Integer, String, VARCHAR, DateTime, Text, ForeignKey, Date
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class StudentAddress(Base):
    """tbl_cp_student_address - Student address records."""
    __tablename__ = "tbl_cp_student_address"

    row_id = Column(Integer, primary_key=True, autoincrement=True)
    address_id = Column(Integer, nullable=False, unique=True)
    student_id = Column(Integer, nullable=False)
    address_line_1 = Column(VARCHAR(255), nullable=False)
    address_line_2 = Column(VARCHAR(255), default='')
    care_of = Column(VARCHAR(255), default='')
    landmark = Column(VARCHAR(255), default='No Landmark')
    pincode_id = Column(Integer, nullable=False)
    latitude = Column(String, default='0.00000000')
    longitude = Column(String, default='0.00000000')
    address_type = Column(VARCHAR(50), nullable=False, default='current')
    address_expiry = Column(String, default='9999-12-31')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
