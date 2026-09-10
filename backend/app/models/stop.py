from sqlalchemy import Column, Integer, String, Float, Time, Boolean
from app.database import Base


class Stop(Base):
    __tablename__ = "stops"

    stop_id = Column(String, primary_key=True, index=True)
    stop_name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    student_count = Column(Integer, default=0)
    attendance_probability = Column(Float, default=0.9)
    pickup_window_start = Column(String)   # "HH:MM"
    pickup_window_end = Column(String)
    dropoff_window_start = Column(String)
    dropoff_window_end = Column(String)
    service_time_minutes = Column(Float, default=2.0)
    priority = Column(Integer, default=1)  # 1=high, 2=medium, 3=low
    historical_delay_probability = Column(Float, default=0.05)
    is_active = Column(Boolean, default=True)
    zone = Column(String, default="A")
