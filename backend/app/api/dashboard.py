"""Dashboard API — KPI cards and summary metrics."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func

from app.database import get_db
from app.api.auth import get_current_user
from app.models.stop import Stop
from app.models.bus import Bus
from app.models.driver import Driver
from app.models.route import Route, RouteStop
from app.models.optimization_run import OptimizationRun
from app.models.fallback_event import FallbackEvent

router = APIRouter()


@router.get("")
async def get_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    n_stops = db.query(Stop).count()
    n_buses = db.query(Bus).count()
    n_drivers = db.query(Driver).filter(Driver.availability == True).count()
    n_students_expected = db.query(
        sql_func.sum(Stop.student_count * Stop.attendance_probability)
    ).scalar() or 0

    # Latest baseline run
    baseline_run = db.query(OptimizationRun).filter(
        OptimizationRun.optimization_type == "baseline"
    ).order_by(OptimizationRun.created_at.desc()).first()

    # Latest multiobjective run
    mo_run = db.query(OptimizationRun).filter(
        OptimizationRun.optimization_type == "multiobjective"
    ).order_by(OptimizationRun.created_at.desc()).first()

    # Routes from latest runs
    baseline_routes = []
    mo_routes = []
    if baseline_run:
        baseline_routes = db.query(Route).filter(Route.optimization_run_id == baseline_run.run_id).all()
    if mo_run:
        mo_routes = db.query(Route).filter(Route.optimization_run_id == mo_run.run_id).all()

    def agg_routes(routes):
        if not routes:
            return {}
        n = len(routes)
        total_dist = sum(r.total_distance_km for r in routes)
        total_dur = sum(r.total_duration_minutes for r in routes)
        avg_otp = sum(r.on_time_probability for r in routes) / n
        cap_viol = sum(r.capacity_violations for r in routes)
        tw_viol = sum(r.time_window_violations for r in routes)
        shift_viol = sum(r.shift_violations for r in routes)
        avg_rel = sum(r.reliability_score for r in routes) / n
        return {
            "n_routes": n,
            "total_distance_km": round(total_dist, 2),
            "avg_distance_km": round(total_dist / n, 2),
            "total_duration_minutes": round(total_dur, 1),
            "avg_duration_minutes": round(total_dur / n, 1),
            "avg_on_time_probability": round(avg_otp * 100, 1),
            "capacity_violations": cap_viol,
            "time_window_violations": tw_viol,
            "shift_violations": shift_viol,
            "avg_reliability_score": round(avg_rel * 100, 1),
        }

    baseline_agg = agg_routes(baseline_routes)
    mo_agg = agg_routes(mo_routes)

    # Active fallback events
    active_fallbacks = db.query(FallbackEvent).filter(FallbackEvent.resolved == False).count()

    # System status (derived from latest fallback events)
    fallback_types = [f.event_type for f in
                       db.query(FallbackEvent).filter(FallbackEvent.resolved == False).all()]
    system_status = {
        "gps": "OFFLINE" if "gps_failure" in fallback_types else "ONLINE",
        "network": "OFFLINE" if "network_failure" in fallback_types else "ONLINE",
        "attendance_feed": "OFFLINE" if "attendance_feed_failure" in fallback_types else "ONLINE",
        "traffic_feed": "OFFLINE" if "traffic_feed_failure" in fallback_types else "ONLINE",
    }

    return {
        "summary": {
            "total_buses": n_buses,
            "total_drivers": n_drivers,
            "total_stops": n_stops,
            "expected_students_today": round(float(n_students_expected), 0),
            "active_fallback_events": active_fallbacks,
            "data_ready": n_stops > 0,
            "has_baseline": baseline_run is not None,
            "has_optimized": mo_run is not None,
        },
        "baseline": baseline_agg,
        "optimized": mo_agg,
        "system_status": system_status,
        "targets": {
            "on_time_target": 95.0,
            "capacity_violations_target": 0,
            "workload_imbalance_target": 20.0,
            "distance_increase_max_pct": 15.0,
        },
    }
