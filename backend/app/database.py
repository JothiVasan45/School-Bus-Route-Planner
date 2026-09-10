"""
Database configuration and initialization for School-Bus Route Planner.
Uses SQLite via SQLAlchemy for simplicity and offline-first operation.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Use environment variable or default to local SQLite file
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./school_bus.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed for SQLite
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency injection for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables on startup."""
    from app.models import (  # noqa: F401 – import to register models
        stop, student, bus, driver, travel_time,
        route, optimization_run, simulation_result,
        constraint_violation, override as override_model,
        fallback_event, sync_queue, validation_feedback,
        experiment_result
    )
    Base.metadata.create_all(bind=engine)
    print("[OK] Database initialized")
