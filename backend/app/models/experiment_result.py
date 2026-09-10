from sqlalchemy import Column, String, Integer, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base


class ExperimentResult(Base):
    __tablename__ = "experiment_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String, index=True)
    scenario_name = Column(String)
    scenario_index = Column(Integer)
    attendance_scenario = Column(String)
    traffic_condition = Column(String)
    optimization_type = Column(String)   # baseline | multiobjective
    total_distance_km = Column(Float)
    total_duration_minutes = Column(Float)
    on_time_probability = Column(Float)
    reliability_score = Column(Float)
    capacity_violations = Column(Integer)
    time_window_violations = Column(Integer)
    shift_violations = Column(Integer)
    workload_variance = Column(Float)
    workload_imbalance = Column(Float)
    avg_driver_workload = Column(Float)
    max_driver_workload = Column(Float)
    min_driver_workload = Column(Float)
    solve_time_seconds = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
