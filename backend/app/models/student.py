from sqlalchemy import Column, Integer, String, Float, Boolean
from app.database import Base


class Student(Base):
    __tablename__ = "students"

    student_id = Column(String, primary_key=True, index=True)
    stop_id = Column(String, index=True)
    attendance_probability = Column(Float, default=0.9)
    weekday = Column(String, default="all")   # all / monday / etc.
    expected_attendance = Column(Float, default=0.9)
    name = Column(String)
    grade = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)
