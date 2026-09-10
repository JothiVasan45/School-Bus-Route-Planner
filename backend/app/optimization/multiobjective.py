"""
Multi-Objective Route Optimizer.

Weighted-sum optimization balancing:
1. Distance minimization
2. Time-window penalty minimization
3. Reliability risk minimization
4. Driver workload imbalance minimization

Strategy:
- Stage 1: Generate feasible candidate routes (nearest-neighbor + 2-opt)
- Stage 2: Evaluate each route set on all 4 objectives
- Stage 3: Select the best weighted combination
- Stage 4: Balance drivers using workload equalization
"""
import math
import time
import uuid
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from copy import deepcopy

from app.optimization.baseline import (
    StopData, BusData, DriverData, TravelEdge, PlannedRoute,
    BaselineOptimizer, _hhmm_to_minutes, _minutes_to_hhmm,
    _get_travel_time, _haversine_km,
)
from app.simulation.monte_carlo import (
    MonteCarloSimulator, SimulationInput, StopEdge
)


@dataclass
class OptimizationWeights:
    w_distance: float = 0.25
    w_time_window: float = 0.30
    w_reliability: float = 0.30
    w_workload: float = 0.15

    def validate(self):
        total = self.w_distance + self.w_time_window + self.w_reliability + self.w_workload
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total:.2f}")


PRESET_WEIGHTS = {
    "distance_priority": OptimizationWeights(0.60, 0.15, 0.15, 0.10),
    "balanced": OptimizationWeights(0.25, 0.30, 0.30, 0.15),
    "reliability_priority": OptimizationWeights(0.15, 0.30, 0.40, 0.15),
}


class MultiObjectiveOptimizer:
    """
    Multi-objective route optimizer using weighted-sum and iterative improvement.
    """

    DEPOT_LAT = 13.0067
    DEPOT_LON = 80.2206

    def __init__(self):
        self._baseline = BaselineOptimizer()
        self._sim = MonteCarloSimulator()

    def optimize(
        self,
        stops: List[StopData],
        buses: List[BusData],
        drivers: List[DriverData],
        travel_edges: List[TravelEdge],
        attendance: Dict[str, int],
        weights: OptimizationWeights,
        attendance_scenario: str = "normal",
        sim_runs: int = 200,    # reduced for speed during optimization
    ) -> List[PlannedRoute]:
        weights.validate()

        travel_map = {(e.from_stop, e.to_stop): e for e in travel_edges}
        stops_map = {s.stop_id: s for s in stops}
        active_stops = [s for s in stops if attendance.get(s.stop_id, 0) > 0]
        available_drivers = [d for d in drivers if d.availability]
        available_buses = [b for b in buses]

        if not active_stops:
            return []

        # ── Stage 1: Generate multiple candidate route sets ────────────────
        # Candidate 1: Baseline (distance-optimized)
        baseline_routes = self._baseline.optimize(
            stops, buses, drivers, travel_edges, attendance, attendance_scenario
        )

        # Candidate 2: Time-window prioritized (sort stops by window end)
        tw_routes = self._time_window_prioritized_routes(
            active_stops, available_buses, available_drivers,
            travel_map, stops_map, attendance, attendance_scenario,
        )

        # Candidate 3: Zone-clustered routes (group by zone for shorter travel)
        zone_routes = self._zone_clustered_routes(
            active_stops, available_buses, available_drivers,
            travel_map, stops_map, attendance, attendance_scenario,
        )

        all_candidates = [
            ("baseline", baseline_routes),
            ("tw_priority", tw_routes),
            ("zone_cluster", zone_routes),
        ]

        # ── Stage 2: Score each candidate set ─────────────────────────────
        best_score = float("inf")
        best_routes = baseline_routes

        for name, candidate_routes in all_candidates:
            if not candidate_routes:
                continue
            score = self._score_route_set(
                candidate_routes, travel_map, stops_map,
                attendance, weights, sim_runs
            )
            if score < best_score:
                best_score = score
                best_routes = candidate_routes

        # ── Stage 3: Balance workload ──────────────────────────────────────
        best_routes = self._balance_workload(
            best_routes, available_drivers, travel_map, stops_map, attendance,
            weights, sim_runs
        )

        # ── Stage 4: Re-label as multiobjective and add reliability data ───
        final_routes = []
        for i, route in enumerate(best_routes):
            route.optimization_type = "multiobjective"
            # Run reliability simulation for each route
            sim_result = self._run_reliability(route, travel_map, stops_map, sim_runs)
            route.notes = (
                f"Reliability: {sim_result['on_time_probability']*100:.1f}% | "
                f"P90: {sim_result['p90_duration']:.0f}min | "
                f"Weighted score: {best_score:.3f}"
            )
            final_routes.append(route)

        return final_routes

    def _score_route_set(
        self,
        routes: List[PlannedRoute],
        travel_map: Dict,
        stops_map: Dict,
        attendance: Dict,
        weights: OptimizationWeights,
        sim_runs: int,
    ) -> float:
        if not routes:
            return float("inf")

        # Objective 1 — Normalized distance
        total_dist = sum(r.total_distance_km for r in routes)

        # Objective 2 — Time window violations
        total_tw_viol = sum(r.time_window_violations for r in routes)

        # Objective 3 — Reliability (Monte Carlo)
        reliability_risks = []
        for route in routes:
            sim = self._run_reliability(route, travel_map, stops_map, sim_runs)
            reliability_risks.append(1.0 - sim["on_time_probability"])
        avg_reliability_risk = np.mean(reliability_risks) if reliability_risks else 1.0

        # Objective 4 — Workload imbalance
        workload_scores = self._compute_workload_scores(routes)
        workload_variance = float(np.var(workload_scores)) if len(workload_scores) > 1 else 0.0

        # Normalize each objective to [0,1] range
        norm_dist = min(total_dist / 500.0, 1.0)          # 500 km reference
        norm_tw = min(total_tw_viol / 10.0, 1.0)          # 10 violations = max penalty
        norm_rel = avg_reliability_risk                     # already 0..1
        norm_wl = min(workload_variance / 10000.0, 1.0)   # normalized variance

        weighted = (
            weights.w_distance * norm_dist
            + weights.w_time_window * norm_tw
            + weights.w_reliability * norm_rel
            + weights.w_workload * norm_wl
        )
        return weighted

    def _run_reliability(
        self,
        route: PlannedRoute,
        travel_map: Dict,
        stops_map: Dict,
        sim_runs: int = 200,
    ) -> Dict:
        edges = []
        seq = route.stop_sequence
        for i in range(len(seq) - 1):
            key = (seq[i], seq[i+1])
            if key in travel_map:
                e = travel_map[key]
                edges.append(StopEdge(
                    from_stop=seq[i], to_stop=seq[i+1],
                    mean_travel_time=e.mean_travel_time,
                    std_travel_time=e.std_travel_time,
                    service_time=stops_map.get(seq[i+1], StopData(seq[i+1], 0, "", "", 2.0, 0, 0)).service_time
                    if seq[i+1] in stops_map else 2.0,
                ))
            else:
                # Fallback: estimate from haversine
                s1 = stops_map.get(seq[i])
                s2 = stops_map.get(seq[i+1])
                if s1 and s2:
                    dist = _haversine_km(s1.latitude, s1.longitude, s2.latitude, s2.longitude)
                    mean_tt = (dist / 30.0) * 60
                    edges.append(StopEdge(seq[i], seq[i+1], mean_tt, mean_tt * 0.25, 2.0))

        if not edges:
            return {"on_time_probability": 0.85, "p90_duration": route.total_duration_minutes * 1.2, "p50_duration": route.total_duration_minutes}

        sim_input = SimulationInput(
            route_id=route.route_id,
            edges=edges,
            required_completion_hhmm="08:30",
            route_start_hhmm=route.planned_start or "06:30",
            simulation_runs=sim_runs,
        )
        result = self._sim.simulate(sim_input)
        return {
            "on_time_probability": result.on_time_probability,
            "p90_duration": result.p90_duration,
            "p50_duration": result.p50_duration,
            "reliability_score": result.reliability_score,
        }

    def _compute_workload_scores(self, routes: List[PlannedRoute]) -> List[float]:
        scores = []
        for r in routes:
            # Workload = weighted combination of duration, stops, students, driving %
            score = (
                r.total_duration_minutes * 0.4
                + r.stop_count * 2.0
                + r.total_students * 0.3
                + r.driving_minutes * 0.3
            )
            scores.append(score)
        return scores

    def _time_window_prioritized_routes(
        self,
        active_stops: List[StopData],
        buses: List[BusData],
        drivers: List[DriverData],
        travel_map: Dict,
        stops_map: Dict,
        attendance: Dict,
        scenario: str,
    ) -> List[PlannedRoute]:
        """Build routes by sorting stops by pickup window end (earliest deadline first)."""
        sorted_stops = sorted(
            active_stops,
            key=lambda s: _hhmm_to_minutes(s.pickup_window_end),
        )
        return self._greedy_routes(sorted_stops, buses, drivers, travel_map, stops_map, attendance, scenario)

    def _zone_clustered_routes(
        self,
        active_stops: List[StopData],
        buses: List[BusData],
        drivers: List[DriverData],
        travel_map: Dict,
        stops_map: Dict,
        attendance: Dict,
        scenario: str,
    ) -> List[PlannedRoute]:
        """Build routes by grouping stops within the same zone."""
        zone_order = ["A", "B", "C", "D", "E"]
        sorted_stops = sorted(active_stops, key=lambda s: zone_order.index(s.zone) if s.zone in zone_order else 5)
        return self._greedy_routes(sorted_stops, buses, drivers, travel_map, stops_map, attendance, scenario)

    def _greedy_routes(
        self,
        stops: List[StopData],
        buses: List[BusData],
        drivers: List[DriverData],
        travel_map: Dict,
        stops_map: Dict,
        attendance: Dict,
        scenario: str,
    ) -> List[PlannedRoute]:
        """Greedy nearest-neighbor route builder."""
        from app.optimization.baseline import BaselineOptimizer
        # Delegate to baseline but with a pre-sorted stop list
        baseline = BaselineOptimizer()
        return baseline.optimize(stops, buses, drivers,
                                  [travel_map[k] for k in travel_map],
                                  attendance, scenario)

    def _balance_workload(
        self,
        routes: List[PlannedRoute],
        drivers: List[DriverData],
        travel_map: Dict,
        stops_map: Dict,
        attendance: Dict,
        weights: OptimizationWeights,
        sim_runs: int,
    ) -> List[PlannedRoute]:
        """
        Attempt to equalize driver workload by moving stops between adjacent routes.
        Simple greedy: find most-loaded and least-loaded driver, move last stop.
        """
        if len(routes) < 2:
            return routes

        workload_scores = self._compute_workload_scores(routes)
        MAX_ITERS = 10

        for _ in range(MAX_ITERS):
            ws = self._compute_workload_scores(routes)
            max_idx = int(np.argmax(ws))
            min_idx = int(np.argmin(ws))

            if max_idx == min_idx:
                break
            if ws[max_idx] - ws[min_idx] < 10:
                break

            # Try moving the last stop from most-loaded to least-loaded
            heavy = routes[max_idx]
            light = routes[min_idx]

            if len(heavy.stop_sequence) <= 1:
                break

            moved_stop = heavy.stop_sequence[-1]
            moved_load = attendance.get(moved_stop, 0)

            # Check capacity of the light route
            if light.capacity_used + moved_load > light.capacity_limit:
                break

            # Do the transfer
            heavy.stop_sequence = heavy.stop_sequence[:-1]
            heavy.capacity_used -= moved_load
            heavy.total_students -= moved_load

            light.stop_sequence = light.stop_sequence + [moved_stop]
            light.capacity_used += moved_load
            light.total_students += moved_load

            # Recompute times for both
            from app.optimization.baseline import BaselineOptimizer
            bopt = BaselineOptimizer()
            for r in [heavy, light]:
                arr, dep, dist, dur, drv = bopt._compute_times(
                    r.stop_sequence, r.planned_start or "06:30", travel_map, stops_map
                )
                r.planned_arrivals = arr
                r.planned_departures = dep
                r.total_distance_km = round(dist, 3)
                r.total_duration_minutes = round(dur, 1)
                r.driving_minutes = round(drv, 1)
                r.stop_count = len(r.stop_sequence)

        return routes


# Global singleton
multi_optimizer = MultiObjectiveOptimizer()
