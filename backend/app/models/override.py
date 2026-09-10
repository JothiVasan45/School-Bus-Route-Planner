from sqlalchemy import Column, String, Float, DateTime, Integer
from sqlalchemy.sql import func
from app.database import Base


class Override(Base):
    __tablename__ = "overrides"

    id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(String, index=True)
    constraint_id = Column(String)
    constraint_name = Column(String)
    user_role = Column(String)
    user_id = Column(String)
    reason = Column(String)
    previous_value = Column(String)
    new_decision = Column(String)
    approved = Column(String, default="approved")   # approved | rejected
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=True)
    notes = Column(String, default="")
