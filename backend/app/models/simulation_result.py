from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.sql import func
from app.database import Base


class SimulationResult(Base):
    __tablename__ = "simulation_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(String, index=True)
    simulation_runs = Column(Integer, default=500)
    expected_duration = Column(Float)
    p50_duration = Column(Float)
    p90_duration = Column(Float)
    p95_duration = Column(Float)
    min_duration = Column(Float)
    max_duration = Column(Float)
    std_duration = Column(Float)
    late_probability = Column(Float)
    on_time_probability = Column(Float)
    reliability_score = Column(Float)
    time_window = Column(String)   # required completion time HH:MM
    scenarios_on_time = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
