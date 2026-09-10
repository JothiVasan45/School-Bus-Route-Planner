from sqlalchemy import Column, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base


class OptimizationRun(Base):
    __tablename__ = "optimization_runs"

    run_id = Column(String, primary_key=True, index=True)
    optimization_type = Column(String)  # "baseline" | "multiobjective"
    attendance_scenario = Column(String, default="normal")
    w_distance = Column(Float, default=0.25)
    w_time_window = Column(Float, default=0.30)
    w_reliability = Column(Float, default=0.30)
    w_workload = Column(Float, default=0.15)
    total_routes = Column(String, default="0")
    total_distance_km = Column(Float, default=0.0)
    total_duration_minutes = Column(Float, default=0.0)
    avg_reliability = Column(Float, default=0.0)
    avg_on_time_probability = Column(Float, default=0.0)
    total_capacity_violations = Column(String, default="0")
    total_time_window_violations = Column(String, default="0")
    total_shift_violations = Column(String, default="0")
    workload_variance = Column(Float, default=0.0)
    workload_imbalance = Column(Float, default=0.0)
    solve_time_seconds = Column(Float, default=0.0)
    status = Column(String, default="completed")
    created_at = Column(DateTime, server_default=func.now())
    run_parameters = Column(String, default="{}")  # JSON string
