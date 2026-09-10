from sqlalchemy import Column, String, Integer, DateTime, Float
from sqlalchemy.sql import func
from app.database import Base


class SyncQueue(Base):
    __tablename__ = "sync_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(String)
    stop_id = Column(String)
    update_type = Column(String)
    update_data = Column(String, default="{}")
    queued_at = Column(DateTime, server_default=func.now())
    synced = Column(Integer, default=0)   # 0=pending, 1=synced
    synced_at = Column(DateTime, nullable=True)
    driver_id = Column(String)
