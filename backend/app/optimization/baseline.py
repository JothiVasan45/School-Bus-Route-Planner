"""
Baseline Route Optimizer — Minimize Total Distance Only.

Implements a Clarke-Wright Savings Algorithm with OR-Tools fallback.
Respects hard constraints: bus capacity, driver shift, stop assignment.
Does NOT optimize reliability or workload fairness.
"""
import math
import time
import uuid
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class StopData:
    stop_id: str
    student_count: int          # realized attendance for this run
    pickup_window_start: str    # HH:MM
    pickup_window_end: str
    service_time: float         # minutes
    latitude: float
    longitude: float
    zone: str = "A"


@dataclass
class BusData:
    bus_id: str
    capacity: int
    available_start: str   # HH:MM
    available_end: str


@dataclass
class DriverData:
    driver_id: str
    driver_name: str
    shift_start: str
    shift_end: str
    max_shift_minutes: int
    max_driving_minutes: int
    availability: bool


@dataclass
class TravelEdge:
    from_stop: str
    to_stop: str
    distance_km: float
    mean_travel_time: float    # minutes
    std_travel_time: float


@dataclass
class PlannedRoute:
    route_id: str
    bus_id: str
    driver_id: str
    optimization_type: str  # "baseline"
    stop_sequence: List[str]
    planned_arrivals: Dict[str, str]    # stop_id -> HH:MM
    planned_departures: Dict[str, str]
    total_distance_km: float
    total_duration_minutes: float
    capacity_used: int
    capacity_limit: int
    time_window_violations: int
    capacity_violations: int
    shift_violations: int
    driving_minutes: float
    stop_count: int
    total_students: int
    planned_start: str
    planned_end: str
    attendance_scenario: str = "normal"
    notes: str = ""


def _hhmm_to_minutes(t: str) -> float:
    try:
        h, m = t.split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return 0.0


def _minutes_to_hhmm(m: float) -> str:
    total = int(round(m))
    h = total // 60
    mn = total % 60
    return f"{h:02d}:{mn:02d}"


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _get_travel_time(
    from_id: str, to_id: str,
    travel_map: Dict[Tuple[str, str], TravelEdge],
    stops_map: Dict[str, StopData],
) -> Tuple[float, float]:
    """Return (distance_km, travel_time_minutes)."""
    key = (from_id, to_id)
    if key in travel_map:
        edge = travel_map[key]
        return edge.distance_km, edge.mean_travel_time
    # Fallback: haversine estimate at 30 km/h
    s1 = stops_map[from_id]
    s2 = stops_map[to_id]
    dist = _haversine_km(s1.latitude, s1.longitude, s2.latitude, s2.longitude)
    return dist, (dist / 30.0) * 60


class BaselineOptimizer:
    """
    Clarke-Wright Savings VRP baseline.
    Objective: minimize total distance.
    Hard constraints: capacity, driver shifts.
    """

    DEPOT_ID = "SCHOOL"
    DEPOT_LAT = 13.0067
    DEPOT_LON = 80.2206   # Approximate central Chennai school location

    def optimize(
        self,
        stops: List[StopData],
        buses: List[BusData],
        drivers: List[DriverData],
        travel_edges: List[TravelEdge],
        attendance: Dict[str, int],
        attendance_scenario: str = "normal",
    ) -> List[PlannedRoute]:
        start_t = time.time()

        # Build lookup maps
        stops_map = {s.stop_id: s for s in stops}
        travel_map = {(e.from_stop, e.to_stop): e for e in travel_edges}
        available_drivers = [d for d in drivers if d.availability]
        available_buses = [b for b in buses]

        # Filter stops with actual attendance > 0
        active_stops = [s for s in stops if attendance.get(s.stop_id, 0) > 0]

        if not active_stops:
            return []

        # ── Step 1: Clarke-Wright Savings ─────────────────────────────────
        savings = self._compute_savings(active_stops, travel_map, stops_map)

        # ── Step 2: Build initial routes (one stop per bus) ───────────────
        routes_stops = [[s.stop_id] for s in active_stops]  # each stop its own route

        # ── Step 3: Merge routes using savings list ────────────────────────
        route_of = {s.stop_id: i for i, r in enumerate(routes_stops) for s in [active_stops[i]] if s.stop_id == r[0]}
        route_of = {}
        for i, r in enumerate(routes_stops):
            for sid in r:
                route_of[sid] = i

        for (saving, s_i, s_j) in savings:
            ri = route_of.get(s_i)
            rj = route_of.get(s_j)
            if ri is None or rj is None or ri == rj:
                continue
            route_i = routes_stops[ri]
            route_j = routes_stops[rj]
            if not route_i or not route_j:
                continue

            # Check if merging is feasible from a capacity standpoint
            # (use max available bus capacity for now — will assign buses later)
            max_cap = max((b.capacity for b in available_buses), default=50)
            load_i = sum(attendance.get(s, 0) for s in route_i)
            load_j = sum(attendance.get(s, 0) for s in route_j)
            if load_i + load_j > max_cap:
                continue

            # Merge: s_i must be at the end of route_i, s_j at start of route_j
            # OR reverse one of the routes
            merged = None
            if route_i[-1] == s_i and route_j[0] == s_j:
                merged = route_i + route_j
            elif route_i[0] == s_i and route_j[-1] == s_j:
                merged = route_j + route_i
            elif route_i[-1] == s_i and route_j[-1] == s_j:
                merged = route_i + list(reversed(route_j))
            elif route_i[0] == s_i and route_j[0] == s_j:
                merged = list(reversed(route_i)) + route_j

            if merged is None:
                continue

            new_idx = ri
            routes_stops[ri] = merged
            routes_stops[rj] = []
            for sid in route_j:
                route_of[sid] = new_idx

        # Remove empty routes
        routes_stops = [r for r in routes_stops if r]

        # ── Step 4: Split oversized routes by bus capacity ─────────────────
        split_routes = []
        for route in routes_stops:
            current = []
            current_load = 0
            max_cap = 50  # will assign proper cap later
            for sid in route:
                load = attendance.get(sid, 0)
                if current_load + load > max_cap and current:
                    split_routes.append(current)
                    current = [sid]
                    current_load = load
                else:
                    current.append(sid)
                    current_load += load
            if current:
                split_routes.append(current)

        # ── Step 5: Apply 2-opt improvements per route ─────────────────────
        improved_routes = []
        for route in split_routes:
            if len(route) > 3:
                route = self._two_opt(route, travel_map, stops_map)
            improved_routes.append(route)

        # ── Step 6: Assign buses and drivers ──────────────────────────────
        planned_routes = []
        n_vehicles = min(len(improved_routes), len(available_buses), len(available_drivers))

        for idx in range(n_vehicles):
            route_stops_ids = improved_routes[idx]
            bus = available_buses[idx]
            driver = available_drivers[idx]

            load = sum(attendance.get(sid, 0) for sid in route_stops_ids)
            cap_viol = 1 if load > bus.capacity else 0

            # Compute planned times
            arrivals, departures, total_dist, total_dur, driving_dur = self._compute_times(
                route_stops_ids, driver.shift_start, travel_map, stops_map
            )

            planned_end = _minutes_to_hhmm(
                _hhmm_to_minutes(driver.shift_start) + total_dur
            )
            shift_viol = 1 if total_dur > driver.max_shift_minutes else 0
            driving_viol = 1 if driving_dur > driver.max_driving_minutes else 0

            # Check time window violations
            tw_viol = 0
            for sid in route_stops_ids:
                stop = stops_map.get(sid)
                arr = arrivals.get(sid, "")
                if stop and arr:
                    a_min = _hhmm_to_minutes(arr)
                    ws = _hhmm_to_minutes(stop.pickup_window_start)
                    we = _hhmm_to_minutes(stop.pickup_window_end)
                    if a_min < ws or a_min > we:
                        tw_viol += 1

            pr = PlannedRoute(
                route_id=f"R{idx+1:02d}-{str(uuid.uuid4())[:6]}",
                bus_id=bus.bus_id,
                driver_id=driver.driver_id,
                optimization_type="baseline",
                stop_sequence=route_stops_ids,
                planned_arrivals=arrivals,
                planned_departures=departures,
                total_distance_km=round(total_dist, 3),
                total_duration_minutes=round(total_dur, 1),
                capacity_used=load,
                capacity_limit=bus.capacity,
                time_window_violations=tw_viol,
                capacity_violations=cap_viol,
                shift_violations=shift_viol + driving_viol,
                driving_minutes=round(driving_dur, 1),
                stop_count=len(route_stops_ids),
                total_students=load,
                planned_start=driver.shift_start,
                planned_end=planned_end,
                attendance_scenario=attendance_scenario,
            )
            planned_routes.append(pr)

        # Handle leftover routes if buses run out
        for idx in range(n_vehicles, len(improved_routes)):
            route_stops_ids = improved_routes[idx]
            load = sum(attendance.get(sid, 0) for sid in route_stops_ids)
            pr = PlannedRoute(
                route_id=f"R{idx+1:02d}-{str(uuid.uuid4())[:6]}",
                bus_id="UNASSIGNED",
                driver_id="UNASSIGNED",
                optimization_type="baseline",
                stop_sequence=route_stops_ids,
                planned_arrivals={},
                planned_departures={},
                total_distance_km=0.0,
                total_duration_minutes=0.0,
                capacity_used=load,
                capacity_limit=0,
                time_window_violations=0,
                capacity_violations=1,
                shift_violations=0,
                driving_minutes=0.0,
                stop_count=len(route_stops_ids),
                total_students=load,
                planned_start="",
                planned_end="",
                attendance_scenario=attendance_scenario,
                notes="No bus/driver available for this route.",
            )
            planned_routes.append(pr)

        return planned_routes

    def _compute_savings(
        self,
        stops: List[StopData],
        travel_map: Dict,
        stops_map: Dict,
    ) -> List[Tuple[float, str, str]]:
        """Clarke-Wright savings: s(i,j) = d(depot,i) + d(j,depot) - d(i,j)."""
        savings = []
        depot = {"latitude": self.DEPOT_LAT, "longitude": self.DEPOT_LON}

        for i, si in enumerate(stops):
            for j, sj in enumerate(stops):
                if i >= j:
                    continue
                # Distance depot→i, j→depot, i→j
                d_depot_i = _haversine_km(depot["latitude"], depot["longitude"], si.latitude, si.longitude)
                d_j_depot = _haversine_km(sj.latitude, sj.longitude, depot["latitude"], depot["longitude"])
                d_ij, _ = _get_travel_time(si.stop_id, sj.stop_id, travel_map, stops_map)
                saving = d_depot_i + d_j_depot - d_ij
                savings.append((saving, si.stop_id, sj.stop_id))

        savings.sort(key=lambda x: -x[0])
        return savings

    def _two_opt(
        self,
        route: List[str],
        travel_map: Dict,
        stops_map: Dict,
    ) -> List[str]:
        """Simple 2-opt improvement."""
        best = list(route)
        improved = True
        while improved:
            improved = False
            for i in range(1, len(best) - 1):
                for j in range(i + 1, len(best)):
                    new_route = best[:i] + list(reversed(best[i:j+1])) + best[j+1:]
                    if self._route_distance(new_route, travel_map, stops_map) < \
                       self._route_distance(best, travel_map, stops_map):
                        best = new_route
                        improved = True
        return best

    def _route_distance(
        self, route: List[str], travel_map: Dict, stops_map: Dict
    ) -> float:
        total = 0.0
        for i in range(len(route) - 1):
            d, _ = _get_travel_time(route[i], route[i+1], travel_map, stops_map)
            total += d
        return total

    def _compute_times(
        self,
        route: List[str],
        start_hhmm: str,
        travel_map: Dict,
        stops_map: Dict,
    ) -> Tuple[Dict, Dict, float, float, float]:
        """Compute planned arrival/departure times along the route."""
        current_min = _hhmm_to_minutes(start_hhmm)
        arrivals = {}
        departures = {}
        total_dist = 0.0
        driving_dur = 0.0

        prev = None
        for sid in route:
            stop = stops_map.get(sid)
            if prev is not None:
                dist, tt = _get_travel_time(prev, sid, travel_map, stops_map)
                total_dist += dist
                driving_dur += tt
                current_min += tt
            arrivals[sid] = _minutes_to_hhmm(current_min)
            svc = stop.service_time if stop else 2.0
            current_min += svc
            departures[sid] = _minutes_to_hhmm(current_min)
            prev = sid

        total_dur = current_min - _hhmm_to_minutes(start_hhmm)
        return arrivals, departures, total_dist, total_dur, driving_dur


# Global singleton
baseline_optimizer = BaselineOptimizer()
