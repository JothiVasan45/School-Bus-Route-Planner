"""
Optimization API — Run baseline and multi-objective optimization.
"""
import json
import uuid
import time
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator

from app.database import get_db
from app.api.auth import get_current_user, require_admin
from app.models.stop import Stop
from app.models.bus import Bus
from app.models.driver import Driver
from app.models.travel_time import TravelTime
from app.models.route import Route, RouteStop
from app.models.optimization_run import OptimizationRun
from app.optimization.baseline import (
    BaselineOptimizer, StopData, BusData, DriverData, TravelEdge
)
from app.optimization.multiobjective import (
    MultiObjectiveOptimizer, OptimizationWeights
)
from app.services.data_generator import generate_attendance
from app.simulation.monte_carlo import MonteCarloSimulator, SimulationInput, StopEdge

router = APIRouter()
_baseline_opt = BaselineOptimizer()
_multi_opt = MultiObjectiveOptimizer()
_sim = MonteCarloSimulator()


class OptimizeRequest(BaseModel):
    optimization_type: str = "baseline"   # baseline | multiobjective
    attendance_scenario: str = "normal"   # normal | low | high | random | custom
    w_distance: float = 0.25
    w_time_window: float = 0.30
    w_reliability: float = 0.30
    w_workload: float = 0.15
    preset: Optional[str] = None          # distance_priority | balanced | reliability_priority
    run_reliability_sim: bool = True
    sim_runs: int = 500
    seed: int = 42

    @validator("optimization_type")
    def validate_type(cls, v):
        if v not in ("baseline", "multiobjective"):
            raise ValueError("Must be 'baseline' or 'multiobjective'")
        return v


def _load_data(db: Session):
    """Load all required data from database."""
    stops_db = db.query(Stop).filter(Stop.is_active == True).all()
    buses_db = db.query(Bus).filter(Bus.is_active == True).all()
    drivers_db = db.query(Driver).filter(Driver.availability == True).all()
    tt_db = db.query(TravelTime).all()
    return stops_db, buses_db, drivers_db, tt_db


def _to_stop_data(s) -> StopData:
    return StopData(
        stop_id=s.stop_id,
        student_count=s.student_count,
        pickup_window_start=s.pickup_window_start or "06:30",
        pickup_window_end=s.pickup_window_end or "08:00",
        service_time=s.service_time_minutes or 2.0,
        latitude=s.latitude,
        longitude=s.longitude,
        zone=s.zone or "A",
    )


def _to_bus_data(b) -> BusData:
    return BusData(
        bus_id=b.bus_id,
        capacity=b.capacity,
        available_start=b.available_start_time or "06:00",
        available_end=b.available_end_time or "09:30",
    )


def _to_driver_data(d) -> DriverData:
    return DriverData(
        driver_id=d.driver_id,
        driver_name=d.driver_name,
        shift_start=d.shift_start or "06:00",
        shift_end=d.shift_end or "09:30",
        max_shift_minutes=d.max_shift_minutes or 210,
        max_driving_minutes=d.max_driving_minutes or 180,
        availability=d.availability,
    )


def _to_travel_edge(tt) -> TravelEdge:
    return TravelEdge(
        from_stop=tt.from_stop,
        to_stop=tt.to_stop,
        distance_km=tt.distance_km or 0.0,
        mean_travel_time=tt.mean_travel_time or 5.0,
        std_travel_time=tt.std_travel_time or 1.5,
    )


def _save_routes(db: Session, routes, run_id: str, travel_map: dict, stops_map: dict, sim_runs: int):
    """Persist planned routes to the database."""
    # Delete previous routes for this run type
    saved = []
    for pr in routes:
        # Run reliability simulation
        on_time_prob = 0.85
        p90_dur = pr.total_duration_minutes * 1.25
        p50_dur = pr.total_duration_minutes
        reliability_score = 0.85

        if pr.stop_sequence and len(pr.stop_sequence) > 1:
            edges = []
            for i in range(len(pr.stop_sequence) - 1):
                key = (pr.stop_sequence[i], pr.stop_sequence[i+1])
                if key in travel_map:
                    e = travel_map[key]
                    svc = stops_map.get(pr.stop_sequence[i+1], {}).get("service_time_minutes", 2.0)
                    edges.append(StopEdge(pr.stop_sequence[i], pr.stop_sequence[i+1],
                                          e.mean_travel_time, e.std_travel_time, svc))

            if edges:
                sim_inp = SimulationInput(
                    route_id=pr.route_id,
                    edges=edges,
                    required_completion_hhmm="08:30",
                    route_start_hhmm=pr.planned_start or "06:30",
                    simulation_runs=min(sim_runs, 500),
                )
                sim_out = _sim.simulate(sim_inp)
                on_time_prob = sim_out.on_time_probability
                p90_dur = sim_out.p90_duration
                p50_dur = sim_out.p50_duration
                reliability_score = sim_out.reliability_score

        db_route = Route(
            route_id=pr.route_id,
            optimization_run_id=run_id,
            bus_id=pr.bus_id,
            driver_id=pr.driver_id,
            optimization_type=pr.optimization_type,
            total_distance_km=pr.total_distance_km,
            total_duration_minutes=pr.total_duration_minutes,
            total_students=pr.total_students,
            capacity_used=pr.capacity_used,
            capacity_limit=pr.capacity_limit,
            time_window_violations=pr.time_window_violations,
            capacity_violations=pr.capacity_violations,
            shift_violations=pr.shift_violations,
            on_time_probability=on_time_prob,
            p90_duration=p90_dur,
            p50_duration=p50_dur,
            reliability_score=reliability_score,
            driving_minutes=pr.driving_minutes,
            stop_count=pr.stop_count,
            planned_start=pr.planned_start,
            planned_end=pr.planned_end,
            attendance_scenario=pr.attendance_scenario,
            notes=pr.notes,
        )
        db.add(db_route)

        for seq, sid in enumerate(pr.stop_sequence):
            arr = pr.planned_arrivals.get(sid, "")
            dep = pr.planned_departures.get(sid, "")
            stop = stops_map.get(sid)
            if stop:
                ws = stop.get("pickup_window_start", "")
                we = stop.get("pickup_window_end", "")
                def hm(t):
                    try:
                        h, m = t.split(":"); return int(h)*60+int(m)
                    except: return 0
                a_min = hm(arr)
                ws_min = hm(ws)
                we_min = hm(we)
                tw_viol = bool(ws and we and (a_min < ws_min or a_min > we_min))
            else:
                ws = we = ""
                tw_viol = False

            db.add(RouteStop(
                route_id=pr.route_id,
                stop_id=sid,
                sequence=seq,
                planned_arrival=arr,
                planned_departure=dep,
                window_start=ws,
                window_end=we,
                window_violated=tw_viol,
                students_boarded=0,
            ))
        saved.append(pr.route_id)

    db.commit()
    return saved


@router.post("/run")
async def run_optimization(
    req: OptimizeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Run baseline or multi-objective optimization."""
    start_t = time.time()

    stops_db, buses_db, drivers_db, tt_db = _load_data(db)
    if not stops_db:
        raise HTTPException(status_code=400, detail="No stop data found. Please generate a dataset first.")

    stops = [_to_stop_data(s) for s in stops_db]
    buses = [_to_bus_data(b) for b in buses_db]
    drivers = [_to_driver_data(d) for d in drivers_db]
    travel_edges = [_to_travel_edge(tt) for tt in tt_db]
    travel_map = {(e.from_stop, e.to_stop): e for e in travel_edges}
    stops_map = {s.stop_id: {"pickup_window_start": s.pickup_window_start,
                              "pickup_window_end": s.pickup_window_end,
                              "service_time_minutes": s.service_time,
                              "latitude": s.latitude, "longitude": s.longitude}
                  for s in stops}

    # Generate attendance
    stops_raw = [{"stop_id": s.stop_id, "student_count": s.student_count,
                   "attendance_probability": 0.85} for s in stops]
    for s_db in stops_db:
        for s_raw in stops_raw:
            if s_raw["stop_id"] == s_db.stop_id:
                s_raw["attendance_probability"] = s_db.attendance_probability
    attendance = generate_attendance(stops_raw, req.attendance_scenario, req.seed)

    # Clear previous routes of same type
    from sqlalchemy import text
    prev_run = db.query(OptimizationRun).filter(
        OptimizationRun.optimization_type == req.optimization_type
    ).order_by(OptimizationRun.created_at.desc()).first()
    if prev_run:
        db.query(RouteStop).filter(
            RouteStop.route_id.in_(
                db.query(Route.route_id).filter(Route.optimization_run_id == prev_run.run_id)
            )
        ).delete(synchronize_session=False)
        db.query(Route).filter(Route.optimization_run_id == prev_run.run_id).delete()
        db.delete(prev_run)
        db.commit()

    # Run optimization
    run_id = str(uuid.uuid4())[:12]

    if req.optimization_type == "baseline":
        routes = _baseline_opt.optimize(stops, buses, drivers, travel_edges, attendance, req.attendance_scenario)
    else:
        # Handle preset weights
        if req.preset and req.preset in ("distance_priority", "balanced", "reliability_priority"):
            from app.optimization.multiobjective import PRESET_WEIGHTS
            weights = PRESET_WEIGHTS[req.preset]
        else:
            weights = OptimizationWeights(
                w_distance=req.w_distance,
                w_time_window=req.w_time_window,
                w_reliability=req.w_reliability,
                w_workload=req.w_workload,
            )
        routes = _multi_opt.optimize(stops, buses, drivers, travel_edges, attendance, weights,
                                      req.attendance_scenario, req.sim_runs)

    # Save routes
    saved_ids = _save_routes(db, routes, run_id, travel_map,
                              {s.stop_id: {"pickup_window_start": s.pickup_window_start,
                                           "pickup_window_end": s.pickup_window_end,
                                           "service_time_minutes": s.service_time}
                               for s in stops},
                              req.sim_runs)

    elapsed = time.time() - start_t

    # Save optimization run record
    import numpy as np
    n_routes = len(routes)
    total_dist = sum(r.total_distance_km for r in routes)
    total_dur = sum(r.total_duration_minutes for r in routes)
    total_tw_viol = sum(r.time_window_violations for r in routes)
    total_cap_viol = sum(r.capacity_violations for r in routes)
    total_shift_viol = sum(r.shift_violations for r in routes)

    db_run = OptimizationRun(
        run_id=run_id,
        optimization_type=req.optimization_type,
        attendance_scenario=req.attendance_scenario,
        w_distance=req.w_distance,
        w_time_window=req.w_time_window,
        w_reliability=req.w_reliability,
        w_workload=req.w_workload,
        total_routes=str(n_routes),
        total_distance_km=round(total_dist, 3),
        total_duration_minutes=round(total_dur, 1),
        total_capacity_violations=str(total_cap_viol),
        total_time_window_violations=str(total_tw_viol),
        total_shift_violations=str(total_shift_viol),
        solve_time_seconds=round(elapsed, 3),
        status="completed",
    )
    db.add(db_run)
    db.commit()

    return {
        "success": True,
        "run_id": run_id,
        "optimization_type": req.optimization_type,
        "n_routes": n_routes,
        "total_distance_km": round(total_dist, 3),
        "total_duration_minutes": round(total_dur, 1),
        "total_capacity_violations": total_cap_viol,
        "total_time_window_violations": total_tw_viol,
        "total_shift_violations": total_shift_viol,
        "solve_time_seconds": round(elapsed, 3),
        "attendance_scenario": req.attendance_scenario,
        "route_ids": saved_ids,
    }


@router.get("/list")
async def list_routes(
    optimization_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all computed routes."""
    query = db.query(Route)
    if optimization_type:
        query = query.filter(Route.optimization_type == optimization_type)
    db_routes = query.order_by(Route.created_at.desc()).all()

    result = []
    for r in db_routes:
        route_stops = db.query(RouteStop).filter(RouteStop.route_id == r.route_id).order_by(RouteStop.sequence).all()
        result.append({
            "route_id": r.route_id,
            "bus_id": r.bus_id,
            "driver_id": r.driver_id,
            "optimization_type": r.optimization_type,
            "total_distance_km": r.total_distance_km,
            "total_duration_minutes": r.total_duration_minutes,
            "total_students": r.total_students,
            "capacity_used": r.capacity_used,
            "capacity_limit": r.capacity_limit,
            "time_window_violations": r.time_window_violations,
            "capacity_violations": r.capacity_violations,
            "shift_violations": r.shift_violations,
            "on_time_probability": r.on_time_probability,
            "reliability_score": r.reliability_score,
            "p90_duration": r.p90_duration,
            "p50_duration": r.p50_duration,
            "stop_count": r.stop_count,
            "planned_start": r.planned_start,
            "planned_end": r.planned_end,
            "attendance_scenario": r.attendance_scenario,
            "notes": r.notes,
            "stops": [
                {
                    "stop_id": rs.stop_id,
                    "sequence": rs.sequence,
                    "planned_arrival": rs.planned_arrival,
                    "planned_departure": rs.planned_departure,
                    "window_start": rs.window_start,
                    "window_end": rs.window_end,
                    "window_violated": rs.window_violated,
                }
                for rs in route_stops
            ],
        })
    return result


@router.get("/{route_id}")
async def get_route(
    route_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    r = db.query(Route).filter(Route.route_id == route_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Route not found")

    route_stops = db.query(RouteStop).filter(RouteStop.route_id == route_id).order_by(RouteStop.sequence).all()
    return {
        "route_id": r.route_id,
        "bus_id": r.bus_id,
        "driver_id": r.driver_id,
        "optimization_type": r.optimization_type,
        "total_distance_km": r.total_distance_km,
        "total_duration_minutes": r.total_duration_minutes,
        "total_students": r.total_students,
        "capacity_used": r.capacity_used,
        "capacity_limit": r.capacity_limit,
        "on_time_probability": r.on_time_probability,
        "reliability_score": r.reliability_score,
        "p90_duration": r.p90_duration,
        "p50_duration": r.p50_duration,
        "stop_count": r.stop_count,
        "planned_start": r.planned_start,
        "planned_end": r.planned_end,
        "notes": r.notes,
        "stops": [
            {
                "stop_id": rs.stop_id,
                "sequence": rs.sequence,
                "planned_arrival": rs.planned_arrival,
                "planned_departure": rs.planned_departure,
                "window_start": rs.window_start,
                "window_end": rs.window_end,
                "window_violated": rs.window_violated,
                "is_completed": rs.is_completed,
                "actual_arrival": rs.actual_arrival,
            }
            for rs in route_stops
        ],
    }
