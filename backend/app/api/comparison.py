"""Comparison API — Side-by-side baseline vs multi-objective comparison."""
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.auth import get_current_user
from app.models.route import Route
from app.models.optimization_run import OptimizationRun

router = APIRouter()


@router.get("")
async def get_comparison(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return side-by-side comparison of baseline vs optimized routes."""
    baseline_run = (db.query(OptimizationRun)
                     .filter(OptimizationRun.optimization_type == "baseline")
                     .order_by(OptimizationRun.created_at.desc()).first())
    mo_run = (db.query(OptimizationRun)
               .filter(OptimizationRun.optimization_type == "multiobjective")
               .order_by(OptimizationRun.created_at.desc()).first())

    if not baseline_run or not mo_run:
        raise HTTPException(
            status_code=400,
            detail="Both baseline and multi-objective routes must be generated first."
        )

    baseline_routes = db.query(Route).filter(Route.optimization_run_id == baseline_run.run_id).all()
    mo_routes = db.query(Route).filter(Route.optimization_run_id == mo_run.run_id).all()

    def agg(routes):
        if not routes:
            return {}
        n = len(routes)
        workload_scores = [
            r.total_duration_minutes * 0.4 + r.stop_count * 2.0 + r.total_students * 0.3
            for r in routes
        ]
        return {
            "n_routes": n,
            "total_distance_km": round(sum(r.total_distance_km for r in routes), 2),
            "avg_distance_km": round(sum(r.total_distance_km for r in routes) / n, 2),
            "total_duration_minutes": round(sum(r.total_duration_minutes for r in routes), 1),
            "avg_duration_minutes": round(sum(r.total_duration_minutes for r in routes) / n, 1),
            "on_time_pct": round(sum(r.on_time_probability for r in routes) / n * 100, 1),
            "late_probability_pct": round((1 - sum(r.on_time_probability for r in routes) / n) * 100, 1),
            "capacity_violations": sum(r.capacity_violations for r in routes),
            "time_window_violations": sum(r.time_window_violations for r in routes),
            "shift_violations": sum(r.shift_violations for r in routes),
            "workload_variance": round(float(np.var(workload_scores)), 2) if workload_scores else 0,
            "max_workload": round(max(workload_scores), 2) if workload_scores else 0,
            "avg_workload": round(float(np.mean(workload_scores)), 2) if workload_scores else 0,
            "avg_reliability": round(sum(r.reliability_score for r in routes) / n * 100, 1),
        }

    b = agg(baseline_routes)
    m = agg(mo_routes)

    def improvement(b_val, m_val, higher_is_better=False):
        if b_val == 0:
            return None
        diff = m_val - b_val
        pct = (diff / abs(b_val)) * 100
        if higher_is_better:
            return {"absolute": round(diff, 2), "pct": round(pct, 1), "improved": diff > 0}
        else:
            return {"absolute": round(diff, 2), "pct": round(pct, 1), "improved": diff < 0}

    # Targets
    targets = {
        "on_time_target_pct": 95.0,
        "capacity_violations_target": 0,
        "workload_imbalance_target_pct": 20.0,
        "distance_increase_max_pct": 15.0,
    }

    def target_status(measured, target, higher_is_better=True):
        if higher_is_better:
            return "PASS" if measured >= target else "FAIL"
        else:
            return "PASS" if measured <= target else "FAIL"

    comparison = {
        "baseline": b,
        "optimized": m,
        "improvements": {
            "total_distance_km": improvement(b.get("total_distance_km"), m.get("total_distance_km")),
            "on_time_pct": improvement(b.get("on_time_pct"), m.get("on_time_pct"), higher_is_better=True),
            "capacity_violations": improvement(b.get("capacity_violations"), m.get("capacity_violations")),
            "time_window_violations": improvement(b.get("time_window_violations"), m.get("time_window_violations")),
            "workload_variance": improvement(b.get("workload_variance"), m.get("workload_variance")),
            "avg_reliability": improvement(b.get("avg_reliability"), m.get("avg_reliability"), higher_is_better=True),
        },
        "targets": targets,
        "target_results": [
            {
                "metric": "On-Time Completion",
                "baseline": b.get("on_time_pct"),
                "target": "≥95%",
                "measured": m.get("on_time_pct"),
                "status": target_status(m.get("on_time_pct", 0), 95.0),
            },
            {
                "metric": "Capacity Violations",
                "baseline": b.get("capacity_violations"),
                "target": "0",
                "measured": m.get("capacity_violations"),
                "status": target_status(m.get("capacity_violations", 99), 0, higher_is_better=False),
            },
            {
                "metric": "Time Window Violations",
                "baseline": b.get("time_window_violations"),
                "target": "0",
                "measured": m.get("time_window_violations"),
                "status": target_status(m.get("time_window_violations", 99), 0, higher_is_better=False),
            },
            {
                "metric": "Average Reliability",
                "baseline": b.get("avg_reliability"),
                "target": "≥90%",
                "measured": m.get("avg_reliability"),
                "status": target_status(m.get("avg_reliability", 0), 90.0),
            },
        ],
    }

    return comparison
