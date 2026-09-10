from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime
from sqlalchemy.sql import func
from app.database import Base


class ConstraintViolation(Base):
    __tablename__ = "constraint_violations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(String, index=True)
    constraint_id = Column(String)
    constraint_name = Column(String)
    constraint_type = Column(String)   # HARD | SOFT
    severity = Column(String)          # CRITICAL | WARNING | INFO
    threshold = Column(Float)
    current_value = Column(Float)
    violation = Column(Boolean, default=False)
    penalty = Column(Float, default=0.0)
    override_allowed = Column(Boolean, default=False)
    description = Column(String)
    created_at = Column(DateTime, server_default=func.now())
