from sqlalchemy import Column, String, Integer, Float, Boolean
from app.database import Base


class Bus(Base):
    __tablename__ = "buses"

    bus_id = Column(String, primary_key=True, index=True)
    registration = Column(String)
    capacity = Column(Integer, nullable=False)
    available_start_time = Column(String, default="06:00")   # HH:MM
    available_end_time = Column(String, default="09:00")
    fuel_type = Column(String, default="diesel")
    is_active = Column(Boolean, default=True)
    current_driver_id = Column(String, nullable=True)
    notes = Column(String, default="")
