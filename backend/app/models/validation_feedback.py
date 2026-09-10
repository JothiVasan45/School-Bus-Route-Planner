from sqlalchemy import Column, String, Integer, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base


class ValidationFeedback(Base):
    __tablename__ = "validation_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    respondent_role = Column(String, default="planner")
    q1_route_clarity = Column(Integer)       # 1-5
    q2_operational_realism = Column(Integer)
    q3_workload_useful = Column(Integer)
    q4_comparison_useful = Column(Integer)
    q5_fallback_clear = Column(Integer)
    q6_would_use_daily = Column(Integer)
    overall_score = Column(Float)
    comments = Column(String, default="")
    respondent_name = Column(String, default="Anonymous")
    created_at = Column(DateTime, server_default=func.now())
    is_simulated = Column(Integer, default=1)   # 1 = prototype simulation
