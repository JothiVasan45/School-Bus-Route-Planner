from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base


class FallbackEvent(Base):
    __tablename__ = "fallback_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String)       # gps_failure | network_failure | attendance_feed_failure | traffic_feed_failure
    triggered_by = Column(String, default="system")
    route_id = Column(String, nullable=True)
    driver_id = Column(String, nullable=True)
    fallback_mode = Column(String)    # offline | manual | cached
    description = Column(String)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    data_snapshot = Column(String, default="{}")   # JSON of cached data at event time
