"""
Driver Workload Service.

Calculates workload scores, fairness metrics, and shift utilization for all drivers.
"""
from typing import List, Dict
import numpy as np
from dataclasses import dataclass


@dataclass
class DriverWorkloadResult:
    driver_id: str
    driver_name: str
    route_id: str
    route_duration_minutes: float
    driving_minutes: float
    stop_count: int
    students_served: int
    workload_score: float
    workload_percentage: float    # 0-100
    driving_percentage: float     # driving_minutes / max_driving_minutes
    shift_start: str
    shift_end: str
    shift_utilization: float     # route_duration / max_shift_minutes
    max_shift_minutes: int
    status: str   # OK | WARNING | OVERLOADED


def calculate_workload_score(
    route_duration: float,
    driving_minutes: float,
    stop_count: int,
    student_count: int,
    max_shift_minutes: float = 210,
    max_driving_minutes: float = 180,
    max_stops: float = 25,
    max_students: float = 50,
) -> float:
    """
    Composite workload score (0–100):
    - 40% route duration utilization
    - 30% driving time utilization
    - 15% stop count
    - 15% student count
    """
    dur_score = min(100, (route_duration / max_shift_minutes) * 100)
    drv_score = min(100, (driving_minutes / max_driving_minutes) * 100)
    stop_score = min(100, (stop_count / max_stops) * 100)
    stu_score = min(100, (student_count / max_students) * 100)
    return round(0.40 * dur_score + 0.30 * drv_score + 0.15 * stop_score + 0.15 * stu_score, 2)


class WorkloadService:

    def analyze(
        self,
        routes: List[Dict],
        drivers_map: Dict[str, Dict],   # driver_id -> driver info
    ) -> Dict:
        """
        Analyze workload for all drivers and return fairness metrics.
        """
        results = []

        for route in routes:
            driver_id = route.get("driver_id")
            if not driver_id or driver_id == "UNASSIGNED":
                continue

            driver = drivers_map.get(driver_id, {})
            max_shift = driver.get("max_shift_minutes", 210)
            max_driving = driver.get("max_driving_minutes", 180)

            route_dur = route.get("total_duration_minutes", 0.0)
            driving_min = route.get("driving_minutes", 0.0)
            stop_count = route.get("stop_count", 0)
            students = route.get("total_students", 0)

            score = calculate_workload_score(
                route_dur, driving_min, stop_count, students,
                max_shift, max_driving
            )

            shift_util = round(route_dur / max_shift * 100, 1) if max_shift else 0
            drv_pct = round(driving_min / max_driving * 100, 1) if max_driving else 0

            if score >= 85:
                status = "OVERLOADED"
            elif score >= 65:
                status = "WARNING"
            else:
                status = "OK"

            results.append(DriverWorkloadResult(
                driver_id=driver_id,
                driver_name=driver.get("driver_name", driver_id),
                route_id=route.get("route_id", ""),
                route_duration_minutes=round(route_dur, 1),
                driving_minutes=round(driving_min, 1),
                stop_count=stop_count,
                students_served=students,
                workload_score=score,
                workload_percentage=score,
                driving_percentage=drv_pct,
                shift_start=driver.get("shift_start", "06:00"),
                shift_end=route.get("planned_end", "08:30"),
                shift_utilization=shift_util,
                max_shift_minutes=max_shift,
                status=status,
            ))

        # Fairness metrics
        scores = [r.workload_score for r in results]
        fairness = {}
        if scores:
            fairness = {
                "max_workload": round(max(scores), 2),
                "min_workload": round(min(scores), 2),
                "avg_workload": round(float(np.mean(scores)), 2),
                "workload_variance": round(float(np.var(scores)), 4),
                "workload_std": round(float(np.std(scores)), 2),
                "workload_imbalance": round(max(scores) - min(scores), 2),
                "imbalance_pct": round((max(scores) - min(scores)) / max(max(scores), 1) * 100, 1),
                "fairness_score": round(max(0, 100 - float(np.std(scores))), 1),
                "overloaded_drivers": sum(1 for r in results if r.status == "OVERLOADED"),
                "warning_drivers": sum(1 for r in results if r.status == "WARNING"),
                "ok_drivers": sum(1 for r in results if r.status == "OK"),
            }

        return {
            "drivers": [
                {
                    "driver_id": r.driver_id,
                    "driver_name": r.driver_name,
                    "route_id": r.route_id,
                    "route_duration_minutes": r.route_duration_minutes,
                    "driving_minutes": r.driving_minutes,
                    "stop_count": r.stop_count,
                    "students_served": r.students_served,
                    "workload_score": r.workload_score,
                    "workload_percentage": r.workload_percentage,
                    "driving_percentage": r.driving_percentage,
                    "shift_start": r.shift_start,
                    "shift_end": r.shift_end,
                    "shift_utilization": r.shift_utilization,
                    "max_shift_minutes": r.max_shift_minutes,
                    "status": r.status,
                }
                for r in results
            ],
            "fairness": fairness,
        }


# Global singleton
workload_service = WorkloadService()
