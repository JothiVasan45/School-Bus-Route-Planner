from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base


class Route(Base):
    __tablename__ = "routes"

    route_id = Column(String, primary_key=True, index=True)
    optimization_run_id = Column(String, index=True)
    bus_id = Column(String)
    driver_id = Column(String)
    optimization_type = Column(String)   # "baseline" | "multiobjective"
    total_distance_km = Column(Float, default=0.0)
    total_duration_minutes = Column(Float, default=0.0)
    total_students = Column(Integer, default=0)
    capacity_used = Column(Integer, default=0)
    capacity_limit = Column(Integer, default=0)
    time_window_violations = Column(Integer, default=0)
    capacity_violations = Column(Integer, default=0)
    shift_violations = Column(Integer, default=0)
    # Reliability
    reliability_score = Column(Float, default=0.0)
    on_time_probability = Column(Float, default=0.0)
    p50_duration = Column(Float, default=0.0)
    p90_duration = Column(Float, default=0.0)
    p95_duration = Column(Float, default=0.0)
    # Objective scores
    objective_distance = Column(Float, default=0.0)
    objective_time_window = Column(Float, default=0.0)
    objective_reliability = Column(Float, default=0.0)
    objective_workload = Column(Float, default=0.0)
    weighted_objective = Column(Float, default=0.0)
    # Workload
    workload_score = Column(Float, default=0.0)
    driving_minutes = Column(Float, default=0.0)
    stop_count = Column(Integer, default=0)
    # Metadata
    planned_start = Column(String)
    planned_end = Column(String)
    status = Column(String, default="planned")   # planned / active / completed
    attendance_scenario = Column(String, default="normal")
    created_at = Column(DateTime, server_default=func.now())
    notes = Column(String, default="")


class RouteStop(Base):
    __tablename__ = "route_stops"

    id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(String, index=True)
    stop_id = Column(String)
    sequence = Column(Integer)
    planned_arrival = Column(String)    # HH:MM
    planned_departure = Column(String)
    actual_arrival = Column(String, nullable=True)
    actual_departure = Column(String, nullable=True)
    students_boarded = Column(Integer, default=0)
    window_start = Column(String)
    window_end = Column(String)
    window_violated = Column(Boolean, default=False)
    delay_reason = Column(String, nullable=True)
    is_completed = Column(Boolean, default=False)
