"""
Constraint Engine — Reusable constraint checking for route validation.
Handles both HARD and SOFT constraints with penalties and override tracking.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class ConstraintType(str, Enum):
    HARD = "HARD"
    SOFT = "SOFT"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class Constraint:
    constraint_id: str
    name: str
    constraint_type: ConstraintType
    severity: Severity
    threshold: float
    current_value: float
    violation: bool = False
    penalty: float = 0.0
    override_allowed: bool = False
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "constraint_id": self.constraint_id,
            "name": self.name,
            "type": self.constraint_type.value,
            "severity": self.severity.value,
            "threshold": self.threshold,
            "current_value": self.current_value,
            "violation": self.violation,
            "penalty": self.penalty,
            "override_allowed": self.override_allowed,
            "description": self.description,
        }


@dataclass
class ConstraintCheckResult:
    constraints: List[Constraint] = field(default_factory=list)
    total_penalty: float = 0.0
    hard_violations: int = 0
    soft_violations: int = 0
    feasible: bool = True   # infeasible only if hard constraint violated


class ConstraintEngine:
    """
    Reusable constraint engine that checks all route constraints and returns
    a detailed violation report.
    """

    # Penalties for soft constraint violations
    SOFT_PENALTIES = {
        "preferred_reliability": 50.0,
        "preferred_workload": 30.0,
        "preferred_max_distance": 20.0,
        "preferred_duration": 25.0,
    }

    def check_route(
        self,
        route_stops: list,
        capacity_used: int,
        bus_capacity: int,
        driver_shift_start: str,
        driver_shift_end: str,
        route_start: str,
        route_end: str,
        driving_minutes: float,
        max_driving_minutes: float,
        arrival_times: list,        # list of (stop_id, arrival_hhmm, window_start, window_end)
        reliability_score: float,
        workload_score: float,
        route_distance_km: float,
        route_duration_minutes: float,
        preferred_max_distance_km: float = 80.0,
        preferred_max_duration_minutes: float = 90.0,
        preferred_min_reliability: float = 0.90,
        preferred_max_workload: float = 80.0,
    ) -> ConstraintCheckResult:
        result = ConstraintCheckResult()

        # ── HARD CONSTRAINTS ──────────────────────────────────────────────

        # H1 — Bus Capacity
        cap_violated = capacity_used > bus_capacity
        c = Constraint(
            constraint_id="H1",
            name="Bus Capacity",
            constraint_type=ConstraintType.HARD,
            severity=Severity.CRITICAL,
            threshold=float(bus_capacity),
            current_value=float(capacity_used),
            violation=cap_violated,
            penalty=0.0,
            override_allowed=False,
            description=f"Route load {capacity_used} must not exceed bus capacity {bus_capacity}.",
        )
        result.constraints.append(c)
        if cap_violated:
            result.hard_violations += 1
            result.feasible = False

        # H2 — Driver Shift End
        shift_violated = self._time_exceeds(route_end, driver_shift_end)
        c = Constraint(
            constraint_id="H2",
            name="Driver Shift End",
            constraint_type=ConstraintType.HARD,
            severity=Severity.CRITICAL,
            threshold=self._hhmm_to_minutes(driver_shift_end),
            current_value=self._hhmm_to_minutes(route_end),
            violation=shift_violated,
            penalty=0.0,
            override_allowed=False,
            description=f"Route must end by driver shift end {driver_shift_end}.",
        )
        result.constraints.append(c)
        if shift_violated:
            result.hard_violations += 1
            result.feasible = False

        # H3 — Max Driving Time
        driving_violated = driving_minutes > max_driving_minutes
        c = Constraint(
            constraint_id="H3",
            name="Max Driving Time",
            constraint_type=ConstraintType.HARD,
            severity=Severity.CRITICAL,
            threshold=max_driving_minutes,
            current_value=driving_minutes,
            violation=driving_violated,
            penalty=0.0,
            override_allowed=False,
            description=f"Driving time {driving_minutes:.1f} min must not exceed {max_driving_minutes} min.",
        )
        result.constraints.append(c)
        if driving_violated:
            result.hard_violations += 1
            result.feasible = False

        # H4 — Time Windows (hard: arrival must be within window)
        tw_violations = 0
        for stop_id, arrival, win_start, win_end in arrival_times:
            if win_start and win_end:
                a_min = self._hhmm_to_minutes(arrival)
                ws_min = self._hhmm_to_minutes(win_start)
                we_min = self._hhmm_to_minutes(win_end)
                if a_min < ws_min or a_min > we_min:
                    tw_violations += 1

        tw_violated = tw_violations > 0
        c = Constraint(
            constraint_id="H4",
            name="Time Window Compliance",
            constraint_type=ConstraintType.HARD,
            severity=Severity.CRITICAL,
            threshold=0.0,
            current_value=float(tw_violations),
            violation=tw_violated,
            penalty=0.0,
            override_allowed=False,
            description=f"{tw_violations} stop(s) have hard time-window violations.",
        )
        result.constraints.append(c)
        if tw_violated:
            result.hard_violations += 1
            # Hard time window violations make route infeasible
            result.feasible = False

        # ── SOFT CONSTRAINTS ──────────────────────────────────────────────

        # S1 — Preferred Reliability
        rel_violated = reliability_score < preferred_min_reliability
        rel_penalty = self.SOFT_PENALTIES["preferred_reliability"] * (1.0 - reliability_score) if rel_violated else 0.0
        c = Constraint(
            constraint_id="S1",
            name="Preferred Reliability Threshold",
            constraint_type=ConstraintType.SOFT,
            severity=Severity.WARNING,
            threshold=preferred_min_reliability,
            current_value=reliability_score,
            violation=rel_violated,
            penalty=rel_penalty,
            override_allowed=True,
            description=f"Preferred reliability ≥ {preferred_min_reliability*100:.0f}%. Current: {reliability_score*100:.1f}%.",
        )
        result.constraints.append(c)
        if rel_violated:
            result.soft_violations += 1
            result.total_penalty += rel_penalty

        # S2 — Preferred Workload Balance
        wl_violated = workload_score > preferred_max_workload
        wl_penalty = self.SOFT_PENALTIES["preferred_workload"] * (workload_score / preferred_max_workload - 1.0) if wl_violated else 0.0
        c = Constraint(
            constraint_id="S2",
            name="Preferred Workload Balance",
            constraint_type=ConstraintType.SOFT,
            severity=Severity.WARNING,
            threshold=preferred_max_workload,
            current_value=workload_score,
            violation=wl_violated,
            penalty=wl_penalty,
            override_allowed=True,
            description=f"Preferred max workload score ≤ {preferred_max_workload}. Current: {workload_score:.1f}.",
        )
        result.constraints.append(c)
        if wl_violated:
            result.soft_violations += 1
            result.total_penalty += wl_penalty

        # S3 — Preferred Max Distance
        dist_violated = route_distance_km > preferred_max_distance_km
        dist_penalty = self.SOFT_PENALTIES["preferred_max_distance"] * (route_distance_km / preferred_max_distance_km - 1.0) if dist_violated else 0.0
        c = Constraint(
            constraint_id="S3",
            name="Preferred Max Distance",
            constraint_type=ConstraintType.SOFT,
            severity=Severity.INFO,
            threshold=preferred_max_distance_km,
            current_value=route_distance_km,
            violation=dist_violated,
            penalty=dist_penalty,
            override_allowed=True,
            description=f"Preferred max route distance ≤ {preferred_max_distance_km} km. Current: {route_distance_km:.1f} km.",
        )
        result.constraints.append(c)
        if dist_violated:
            result.soft_violations += 1
            result.total_penalty += dist_penalty

        # S4 — Preferred Route Duration
        dur_violated = route_duration_minutes > preferred_max_duration_minutes
        dur_penalty = self.SOFT_PENALTIES["preferred_duration"] * (route_duration_minutes / preferred_max_duration_minutes - 1.0) if dur_violated else 0.0
        c = Constraint(
            constraint_id="S4",
            name="Preferred Route Duration",
            constraint_type=ConstraintType.SOFT,
            severity=Severity.INFO,
            threshold=preferred_max_duration_minutes,
            current_value=route_duration_minutes,
            violation=dur_violated,
            penalty=dur_penalty,
            override_allowed=True,
            description=f"Preferred max route duration ≤ {preferred_max_duration_minutes} min. Current: {route_duration_minutes:.1f} min.",
        )
        result.constraints.append(c)
        if dur_violated:
            result.soft_violations += 1
            result.total_penalty += dur_penalty

        return result

    @staticmethod
    def _hhmm_to_minutes(t: str) -> float:
        """Convert HH:MM to minutes since midnight."""
        try:
            h, m = t.split(":")
            return int(h) * 60 + int(m)
        except Exception:
            return 0.0

    @staticmethod
    def _time_exceeds(t_actual: str, t_limit: str) -> bool:
        """Returns True if t_actual > t_limit."""
        try:
            def hm(t):
                h, m = t.split(":")
                return int(h) * 60 + int(m)
            return hm(t_actual) > hm(t_limit)
        except Exception:
            return False


# Global singleton
constraint_engine = ConstraintEngine()
