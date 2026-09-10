"""Workload API — Driver workload analysis and fairness metrics."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.auth import get_current_user
from app.models.route import Route
from app.models.driver import Driver
from app.services.workload import workload_service

router = APIRouter()


@router.get("")
async def get_workload(
    optimization_type: str = "multiobjective",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return driver workload analysis for the latest optimization run."""
    routes = (db.query(Route)
               .filter(Route.optimization_type == optimization_type)
               .order_by(Route.created_at.desc())
               .limit(20).all())

    if not routes:
        routes = db.query(Route).order_by(Route.created_at.desc()).limit(20).all()

    drivers = db.query(Driver).all()
    drivers_map = {
        d.driver_id: {
            "driver_id": d.driver_id,
            "driver_name": d.driver_name,
            "shift_start": d.shift_start,
            "shift_end": d.shift_end,
            "max_shift_minutes": d.max_shift_minutes,
            "max_driving_minutes": d.max_driving_minutes,
        }
        for d in drivers
    }

    route_dicts = [
        {
            "route_id": r.route_id,
            "driver_id": r.driver_id,
            "total_duration_minutes": r.total_duration_minutes,
            "driving_minutes": r.driving_minutes,
            "stop_count": r.stop_count,
            "total_students": r.total_students,
            "planned_start": r.planned_start,
            "planned_end": r.planned_end,
        }
        for r in routes
    ]

    result = workload_service.analyze(route_dicts, drivers_map)
    return result
