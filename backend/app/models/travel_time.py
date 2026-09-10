from sqlalchemy import Column, String, Float
from app.database import Base


class TravelTime(Base):
    __tablename__ = "travel_times"

    id = Column(String, primary_key=True)     # f"{from_stop}_{to_stop}"
    from_stop = Column(String, index=True)
    to_stop = Column(String, index=True)
    distance_km = Column(Float)
    mean_travel_time = Column(Float)           # minutes
    std_travel_time = Column(Float)            # minutes
    p50_time = Column(Float)
    p90_time = Column(Float)
    p95_time = Column(Float)
    traffic_condition = Column(String, default="normal")  # normal / heavy / light
    lognormal_mu = Column(Float)               # computed from mean & std
    lognormal_sigma = Column(Float)
