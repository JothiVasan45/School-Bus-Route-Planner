from sqlalchemy import Column, String, Integer, Float, Boolean
from app.database import Base


class Driver(Base):
    __tablename__ = "drivers"

    driver_id = Column(String, primary_key=True, index=True)
    driver_name = Column(String, nullable=False)
    shift_start = Column(String, default="06:00")     # HH:MM
    shift_end = Column(String, default="09:30")
    max_shift_minutes = Column(Integer, default=210)
    max_driving_minutes = Column(Integer, default=180)
    break_requirement = Column(Integer, default=30)   # minutes after X hours
    availability = Column(Boolean, default=True)
    license_type = Column(String, default="Heavy")
    phone = Column(String, default="")
    years_experience = Column(Integer, default=5)
    workload_score = Column(Float, default=0.0)
