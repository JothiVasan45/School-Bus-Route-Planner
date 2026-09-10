"""Experiments API — Run multi-scenario experiment suite."""
import uuid
import time
import random
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.api.auth import get_current_user, require_admin
from app.models.experiment_result import ExperimentResult
from app.models.stop import Stop
from app.models.bus import Bus
from app.models.driver import Driver
from app.models.travel_time import TravelTime
from app.optimization.baseline import BaselineOptimizer, StopData, BusData, DriverData, TravelEdge
from app.optimization.multiobjective import MultiObjectiveOptimizer, OptimizationWeights
from app.services.workload import workload_service
from app.services.data_generator import generate_attendance
from app.simulation.monte_carlo import MonteCarloSimulator, SimulationInput, StopEdge as SimEdge

router = APIRouter()
_baseline = BaselineOptimizer()
_multi = MultiObjectiveOptimizer()
_sim = MonteCarloSimulator()


class ExperimentRequest(BaseModel):
    n_scenarios: int = 20
    sim_runs_per_scenario: int = 100
    seed: int = 42


@router.post("/run")
async def run_experiments(
    req: ExperimentRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Run the full experiment suite comparing baseline vs multi-objective."""
    stops_db = db.query(Stop).filter(Stop.is_active == True).all()
    buses_db = db.query(Bus).filter(Bus.is_active == True).all()
    drivers_db = db.query(Driver).filter(Driver.availability == True).all()
    tt_db = db.query(TravelTime).all()

    if not stops_db:
        raise HTTPException(status_code=400, detail="No data found. Generate dataset first.")

    stops = [StopData(s.stop_id, s.student_count, s.pickup_window_start or "06:30",
                       s.pickup_window_end or "08:00", s.service_time_minutes or 2.0,
                       s.latitude, s.longitude, s.zone or "A") for s in stops_db]
    buses = [BusData(b.bus_id, b.capacity, b.available_start_time or "06:00",
                      b.available_end_time or "09:30") for b in buses_db]
    drivers = [DriverData(d.driver_id, d.driver_name, d.shift_start or "06:00",
                           d.shift_end or "09:30", d.max_shift_minutes or 210,
                           d.max_driving_minutes or 180, d.availability) for d in drivers_db]
    travel_edges = [TravelEdge(tt.from_stop, tt.to_stop, tt.distance_km or 0,
                                tt.mean_travel_time or 5, tt.std_travel_time or 1.5) for tt in tt_db]
    travel_map = {(e.from_stop, e.to_stop): e for e in travel_edges}

    stops_raw = [{"stop_id": s.stop_id, "student_count": s.student_count,
                   "attendance_probability": sdb.attendance_probability}
                  for s, sdb in zip(stops, stops_db)]

    experiment_id = str(uuid.uuid4())[:12]
    scenarios = [
        ("normal", "normal"),
        ("low", "normal"),
        ("high", "normal"),
        ("random", "normal"),
        ("normal", "heavy"),
        ("low", "heavy"),
        ("high", "light"),
        ("random", "heavy"),
        ("normal", "light"),
        ("random", "light"),
    ]
    # Extend to n_scenarios
    while len(scenarios) < req.n_scenarios:
        sc = random.choice(["normal", "low", "high", "random"])
        tc = random.choice(["normal", "heavy", "light"])
        scenarios.append((sc, tc))
    scenarios = scenarios[:req.n_scenarios]

    weights = OptimizationWeights(0.25, 0.30, 0.30, 0.15)
    drivers_map = {d.driver_id: {"driver_id": d.driver_id, "driver_name": d.driver_name,
                                   "shift_start": d.shift_start, "max_shift_minutes": d.max_shift_minutes,
                                   "max_driving_minutes": d.max_driving_minutes} for d in drivers}

    all_results = []
    start_t = time.time()

    for idx, (att_scenario, traffic) in enumerate(scenarios):
        seed_i = req.seed + idx
        rng = np.random.default_rng(seed_i)

        # Modify travel times for traffic condition
        traffic_mult = {"normal": 1.0, "heavy": 1.35, "light": 0.80}[traffic]
        traffic_edges = [
            TravelEdge(e.from_stop, e.to_stop, e.distance_km,
                       e.mean_travel_time * traffic_mult * float(rng.uniform(0.9, 1.1)),
                       e.std_travel_time * traffic_mult) for e in travel_edges
        ]

        attendance = generate_attendance(stops_raw, att_scenario, seed_i)

        for opt_type in ["baseline", "multiobjective"]:
            t0 = time.time()
            if opt_type == "baseline":
                routes = _baseline.optimize(stops, buses, drivers, traffic_edges, attendance, att_scenario)
            else:
                routes = _multi.optimize(stops, buses, drivers, traffic_edges, attendance, weights, att_scenario, req.sim_runs_per_scenario)
            solve_t = time.time() - t0

            if not routes:
                continue

            route_dicts = [{"route_id": r.route_id, "driver_id": r.driver_id,
                            "total_duration_minutes": r.total_duration_minutes,
                            "driving_minutes": r.driving_minutes, "stop_count": r.stop_count,
                            "total_students": r.total_students, "planned_start": r.planned_start,
                            "planned_end": r.planned_end} for r in routes]
            workload_result = workload_service.analyze(route_dicts, drivers_map)
            fairness = workload_result.get("fairness", {})

            # Quick reliability estimate
            on_time_probs = []
            for r in routes[:5]:  # sample first 5 routes for speed
                edges_sim = []
                seq = r.stop_sequence
                for i in range(len(seq) - 1):
                    key = (seq[i], seq[i+1])
                    if key in {(e.from_stop, e.to_stop): e for e in traffic_edges}:
                        te = {(e.from_stop, e.to_stop): e for e in traffic_edges}[key]
                        edges_sim.append(SimEdge(seq[i], seq[i+1], te.mean_travel_time, te.std_travel_time, 2.0))
                if edges_sim:
                    sim_out = _sim.simulate(SimulationInput(r.route_id, edges_sim, "08:30", r.planned_start or "06:30", req.sim_runs_per_scenario))
                    on_time_probs.append(sim_out.on_time_probability)
            avg_otp = float(np.mean(on_time_probs)) if on_time_probs else 0.85

            result = ExperimentResult(
                experiment_id=experiment_id,
                scenario_name=f"{att_scenario}_{traffic}",
                scenario_index=idx,
                attendance_scenario=att_scenario,
                traffic_condition=traffic,
                optimization_type=opt_type,
                total_distance_km=sum(r.total_distance_km for r in routes),
                total_duration_minutes=sum(r.total_duration_minutes for r in routes),
                on_time_probability=avg_otp,
                reliability_score=avg_otp * 0.9,
                capacity_violations=sum(r.capacity_violations for r in routes),
                time_window_violations=sum(r.time_window_violations for r in routes),
                shift_violations=sum(r.shift_violations for r in routes),
                workload_variance=fairness.get("workload_variance", 0),
                workload_imbalance=fairness.get("workload_imbalance", 0),
                avg_driver_workload=fairness.get("avg_workload", 0),
                max_driver_workload=fairness.get("max_workload", 0),
                min_driver_workload=fairness.get("min_workload", 0),
                solve_time_seconds=solve_t,
            )
            db.add(result)
            all_results.append({
                "scenario_index": idx,
                "scenario": att_scenario,
                "traffic": traffic,
                "optimization_type": opt_type,
                "total_distance_km": round(sum(r.total_distance_km for r in routes), 2),
                "on_time_probability": round(avg_otp * 100, 1),
                "capacity_violations": sum(r.capacity_violations for r in routes),
                "workload_variance": round(fairness.get("workload_variance", 0), 2),
            })

    db.commit()
    total_t = time.time() - start_t

    # Aggregate summary
    baseline_results = [r for r in all_results if r["optimization_type"] == "baseline"]
    mo_results = [r for r in all_results if r["optimization_type"] == "multiobjective"]

    def mean_safe(lst, key):
        vals = [x[key] for x in lst if x.get(key) is not None]
        return round(float(np.mean(vals)), 2) if vals else 0.0

    summary = {
        "experiment_id": experiment_id,
        "n_scenarios": len(scenarios),
        "total_runs": len(all_results),
        "total_time_seconds": round(total_t, 2),
        "baseline_avg": {
            "total_distance_km": mean_safe(baseline_results, "total_distance_km"),
            "on_time_probability": mean_safe(baseline_results, "on_time_probability"),
            "capacity_violations": mean_safe(baseline_results, "capacity_violations"),
            "workload_variance": mean_safe(baseline_results, "workload_variance"),
        },
        "optimized_avg": {
            "total_distance_km": mean_safe(mo_results, "total_distance_km"),
            "on_time_probability": mean_safe(mo_results, "on_time_probability"),
            "capacity_violations": mean_safe(mo_results, "capacity_violations"),
            "workload_variance": mean_safe(mo_results, "workload_variance"),
        },
        "results": all_results,
    }
    return summary


@router.get("/results")
async def get_experiment_results(
    experiment_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = db.query(ExperimentResult)
    if experiment_id:
        query = query.filter(ExperimentResult.experiment_id == experiment_id)
    results = query.order_by(ExperimentResult.created_at.desc()).limit(200).all()
    return [
        {
            "id": r.id,
            "experiment_id": r.experiment_id,
            "scenario_name": r.scenario_name,
            "attendance_scenario": r.attendance_scenario,
            "traffic_condition": r.traffic_condition,
            "optimization_type": r.optimization_type,
            "total_distance_km": round(r.total_distance_km, 2),
            "on_time_probability": round(r.on_time_probability * 100, 1),
            "capacity_violations": r.capacity_violations,
            "workload_variance": round(r.workload_variance, 2),
            "workload_imbalance": round(r.workload_imbalance, 2),
        }
        for r in results
    ]
