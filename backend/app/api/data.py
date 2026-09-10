"""
Data API — Upload, generate, and preview the school-bus dataset.
"""
import json
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.api.auth import get_current_user, require_admin
from app.services.data_generator import data_generator
from app.models.stop import Stop
from app.models.student import Student
from app.models.bus import Bus
from app.models.driver import Driver
from app.models.travel_time import TravelTime

router = APIRouter()


class GenerateRequest(BaseModel):
    n_stops: int = 75
    n_students: int = 350
    n_buses: int = 10
    n_drivers: int = 10
    seed: int = 42


def _clear_and_insert(db: Session, data: dict):
    """Clear existing data and insert fresh synthetic dataset."""
    db.query(TravelTime).delete()
    db.query(Student).delete()
    db.query(Stop).delete()
    db.query(Bus).delete()
    db.query(Driver).delete()
    db.commit()

    for s in data["stops"]:
        db.add(Stop(**s))
    for s in data["students"]:
        db.add(Student(**s))
    for b in data["buses"]:
        db.add(Bus(**b))
    for d in data["drivers"]:
        db.add(Driver(**d))
    for tt in data["travel_times"]:
        db.add(TravelTime(**tt))
    db.commit()


@router.post("/generate")
async def generate_dataset(
    req: GenerateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Generate and store a new synthetic dataset."""
    data = data_generator.generate_all(
        n_stops=req.n_stops,
        n_students=req.n_students,
        n_buses=req.n_buses,
        n_drivers=req.n_drivers,
        seed=req.seed,
    )
    _clear_and_insert(db, data)
    return {
        "success": True,
        "message": "Dataset generated successfully.",
        "metadata": data["metadata"],
    }


@router.get("/preview")
async def preview_dataset(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return a preview of the current dataset."""
    stops = db.query(Stop).limit(20).all()
    students = db.query(Student).limit(20).all()
    buses = db.query(Bus).all()
    drivers = db.query(Driver).all()

    n_stops = db.query(Stop).count()
    n_students = db.query(Student).count()
    n_buses = db.query(Bus).count()
    n_drivers = db.query(Driver).count()
    n_tt = db.query(TravelTime).count()

    return {
        "metadata": {
            "n_stops": n_stops,
            "n_students": n_students,
            "n_buses": n_buses,
            "n_drivers": n_drivers,
            "n_travel_time_pairs": n_tt,
        },
        "stops": [
            {
                "stop_id": s.stop_id, "stop_name": s.stop_name,
                "latitude": s.latitude, "longitude": s.longitude,
                "student_count": s.student_count,
                "attendance_probability": s.attendance_probability,
                "pickup_window_start": s.pickup_window_start,
                "pickup_window_end": s.pickup_window_end,
                "service_time_minutes": s.service_time_minutes,
                "priority": s.priority,
                "zone": s.zone,
            }
            for s in stops
        ],
        "students": [
            {
                "student_id": s.student_id, "stop_id": s.stop_id,
                "name": s.name, "grade": s.grade,
                "attendance_probability": s.attendance_probability,
            }
            for s in students
        ],
        "buses": [
            {
                "bus_id": b.bus_id, "registration": b.registration,
                "capacity": b.capacity, "fuel_type": b.fuel_type,
                "available_start_time": b.available_start_time,
                "available_end_time": b.available_end_time,
            }
            for b in buses
        ],
        "drivers": [
            {
                "driver_id": d.driver_id, "driver_name": d.driver_name,
                "shift_start": d.shift_start, "shift_end": d.shift_end,
                "max_shift_minutes": d.max_shift_minutes,
                "max_driving_minutes": d.max_driving_minutes,
                "availability": d.availability,
            }
            for d in drivers
        ],
    }


@router.get("/stops")
async def get_all_stops(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    stops = db.query(Stop).filter(Stop.is_active == True).all()
    return [
        {
            "stop_id": s.stop_id, "stop_name": s.stop_name,
            "latitude": s.latitude, "longitude": s.longitude,
            "student_count": s.student_count,
            "attendance_probability": s.attendance_probability,
            "pickup_window_start": s.pickup_window_start,
            "pickup_window_end": s.pickup_window_end,
            "service_time_minutes": s.service_time_minutes,
            "priority": s.priority, "zone": s.zone,
            "historical_delay_probability": s.historical_delay_probability,
        }
        for s in stops
    ]


@router.get("/buses")
async def get_all_buses(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    buses = db.query(Bus).all()
    return [
        {
            "bus_id": b.bus_id, "registration": b.registration,
            "capacity": b.capacity, "fuel_type": b.fuel_type,
            "available_start_time": b.available_start_time,
            "available_end_time": b.available_end_time,
            "is_active": b.is_active,
        }
        for b in buses
    ]


@router.get("/drivers")
async def get_all_drivers(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    drivers = db.query(Driver).all()
    return [
        {
            "driver_id": d.driver_id, "driver_name": d.driver_name,
            "shift_start": d.shift_start, "shift_end": d.shift_end,
            "max_shift_minutes": d.max_shift_minutes,
            "max_driving_minutes": d.max_driving_minutes,
            "break_requirement": d.break_requirement,
            "availability": d.availability,
        }
        for d in drivers
    ]


@router.get("/stats")
async def get_data_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return high-level dataset statistics."""
    from sqlalchemy import func as sql_func
    n_stops = db.query(Stop).count()
    n_students = db.query(Student).count()
    n_buses = db.query(Bus).count()
    n_drivers = db.query(Driver).count()
    n_tt = db.query(TravelTime).count()
    total_capacity = db.query(sql_func.sum(Bus.capacity)).scalar() or 0
    avg_attendance = db.query(sql_func.avg(Stop.attendance_probability)).scalar() or 0.0
    total_expected_students = db.query(
        sql_func.sum(Stop.student_count * Stop.attendance_probability)
    ).scalar() or 0

    return {
        "n_stops": n_stops,
        "n_students": n_students,
        "n_buses": n_buses,
        "n_drivers": n_drivers,
        "n_travel_time_pairs": n_tt,
        "total_bus_capacity": int(total_capacity),
        "avg_attendance_probability": round(float(avg_attendance), 3),
        "total_expected_daily_students": round(float(total_expected_students), 0),
        "data_ready": n_stops > 0,
    }
