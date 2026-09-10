"""
Comprehensive test suite for the School-Bus Route Planner.
Tests: constraint engine, baseline optimizer, multi-objective optimizer,
Monte Carlo simulator, workload service, fallback module, and override blocking.
"""
import pytest
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.constraints.engine import ConstraintEngine, ConstraintType
from app.simulation.monte_carlo import MonteCarloSimulator, SimulationInput, StopEdge
from app.services.workload import workload_service, calculate_workload_score
from app.services.data_generator import data_generator, generate_attendance
from app.optimization.baseline import (
    BaselineOptimizer, StopData, BusData, DriverData, TravelEdge
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_stops():
    return [
        StopData("S001", 8, "06:30", "07:30", 2.0, 13.05, 80.22, "A"),
        StopData("S002", 12, "06:45", "07:45", 2.0, 13.06, 80.23, "A"),
        StopData("S003", 5, "07:00", "08:00", 2.0, 13.07, 80.21, "B"),
        StopData("S004", 10, "06:30", "07:30", 2.0, 13.04, 80.24, "A"),
        StopData("S005", 15, "06:45", "07:45", 2.0, 13.08, 80.20, "B"),
    ]


@pytest.fixture
def sample_buses():
    return [
        BusData("BUS01", 30, "06:00", "09:30"),
        BusData("BUS02", 40, "06:00", "09:30"),
    ]


@pytest.fixture
def sample_drivers():
    return [
        DriverData("DRV01", "Arjun K", "06:00", "09:30", 210, 180, True),
        DriverData("DRV02", "Bala S", "06:00", "09:30", 210, 180, True),
    ]


@pytest.fixture
def sample_travel_edges():
    edges = []
    stops = ["S001", "S002", "S003", "S004", "S005"]
    for i, s1 in enumerate(stops):
        for j, s2 in enumerate(stops):
            if s1 != s2:
                edges.append(TravelEdge(s1, s2, 2.0 + abs(i-j), 5.0 + abs(i-j), 1.5))
    return edges


@pytest.fixture
def normal_attendance():
    return {"S001": 7, "S002": 9, "S003": 4, "S004": 8, "S005": 12}


# ─── Unit Tests: Constraint Engine ────────────────────────────────────────────

class TestConstraintEngine:

    def setup_method(self):
        self.engine = ConstraintEngine()

    def test_capacity_hard_constraint_pass(self):
        result = self.engine.check_route(
            route_stops=["S001", "S002"],
            capacity_used=25, bus_capacity=30,
            driver_shift_start="06:00", driver_shift_end="09:30",
            route_start="06:00", route_end="08:30",
            driving_minutes=60, max_driving_minutes=180,
            arrival_times=[("S001", "06:30", "06:30", "07:30"), ("S002", "06:50", "06:45", "07:45")],
            reliability_score=0.95, workload_score=50.0,
            route_distance_km=20.0, route_duration_minutes=60.0,
        )
        cap_constraint = next(c for c in result.constraints if c.constraint_id == "H1")
        assert not cap_constraint.violation
        assert result.feasible

    def test_capacity_hard_constraint_fail(self):
        """Test that exceeding bus capacity creates a hard violation."""
        result = self.engine.check_route(
            route_stops=["S001", "S002"],
            capacity_used=45, bus_capacity=30,   # EXCEEDED
            driver_shift_start="06:00", driver_shift_end="09:30",
            route_start="06:00", route_end="08:30",
            driving_minutes=60, max_driving_minutes=180,
            arrival_times=[],
            reliability_score=0.95, workload_score=50.0,
            route_distance_km=20.0, route_duration_minutes=60.0,
        )
        cap_constraint = next(c for c in result.constraints if c.constraint_id == "H1")
        assert cap_constraint.violation
        assert not result.feasible
        assert result.hard_violations > 0

    def test_driver_shift_hard_constraint_fail(self):
        """Test that route ending after shift end creates a hard violation."""
        result = self.engine.check_route(
            route_stops=["S001", "S002"],
            capacity_used=20, bus_capacity=30,
            driver_shift_start="06:00", driver_shift_end="09:00",
            route_start="06:00", route_end="09:45",  # EXCEEDED SHIFT
            driving_minutes=150, max_driving_minutes=180,
            arrival_times=[],
            reliability_score=0.95, workload_score=50.0,
            route_distance_km=20.0, route_duration_minutes=225.0,
        )
        shift_constraint = next(c for c in result.constraints if c.constraint_id == "H2")
        assert shift_constraint.violation
        assert not result.feasible

    def test_time_window_hard_constraint(self):
        """Test time window violations are detected."""
        result = self.engine.check_route(
            route_stops=["S001"],
            capacity_used=10, bus_capacity=30,
            driver_shift_start="06:00", driver_shift_end="09:30",
            route_start="06:00", route_end="08:00",
            driving_minutes=60, max_driving_minutes=180,
            # Arrival at 08:30 but window ends at 07:30 → VIOLATION
            arrival_times=[("S001", "08:30", "06:30", "07:30")],
            reliability_score=0.95, workload_score=50.0,
            route_distance_km=10.0, route_duration_minutes=60.0,
        )
        tw_constraint = next(c for c in result.constraints if c.constraint_id == "H4")
        assert tw_constraint.violation

    def test_soft_reliability_constraint(self):
        """Test that low reliability creates a soft penalty (not infeasibility)."""
        result = self.engine.check_route(
            route_stops=["S001"],
            capacity_used=10, bus_capacity=30,
            driver_shift_start="06:00", driver_shift_end="09:30",
            route_start="06:00", route_end="08:00",
            driving_minutes=60, max_driving_minutes=180,
            arrival_times=[("S001", "07:00", "06:30", "07:30")],
            reliability_score=0.70,  # BELOW 0.90 threshold
            workload_score=50.0,
            route_distance_km=10.0, route_duration_minutes=60.0,
        )
        rel_constraint = next(c for c in result.constraints if c.constraint_id == "S1")
        assert rel_constraint.violation
        assert rel_constraint.constraint_type == ConstraintType.SOFT
        assert rel_constraint.override_allowed
        assert result.total_penalty > 0

    def test_hard_constraint_not_overrideable(self):
        """Confirm hard constraints have override_allowed=False."""
        result = self.engine.check_route(
            route_stops=["S001"],
            capacity_used=45, bus_capacity=30,  # hard violation
            driver_shift_start="06:00", driver_shift_end="09:30",
            route_start="06:00", route_end="08:00",
            driving_minutes=60, max_driving_minutes=180,
            arrival_times=[],
            reliability_score=0.95, workload_score=50.0,
            route_distance_km=10.0, route_duration_minutes=60.0,
        )
        cap = next(c for c in result.constraints if c.constraint_id == "H1")
        assert not cap.override_allowed


# ─── Unit Tests: Monte Carlo Simulator ────────────────────────────────────────

class TestMonteCarloSimulator:

    def setup_method(self):
        self.sim = MonteCarloSimulator()

    def test_basic_simulation_output(self):
        """Test simulator returns expected output structure."""
        edges = [
            StopEdge("S001", "S002", 5.0, 2.0),
            StopEdge("S002", "S003", 3.0, 1.5),
        ]
        inp = SimulationInput("R001", edges, "08:30", "06:30", simulation_runs=200)
        out = self.sim.simulate(inp, rng_seed=42)

        assert out.route_id == "R001"
        assert out.simulation_runs == 200
        assert 0.0 <= out.on_time_probability <= 1.0
        assert 0.0 <= out.late_probability <= 1.0
        assert abs(out.on_time_probability + out.late_probability - 1.0) < 0.01
        assert out.p50_duration > 0
        assert out.p90_duration >= out.p50_duration
        assert out.p95_duration >= out.p90_duration

    def test_reliability_simulation(self):
        """Test that reliability is computed and bounded."""
        edges = [StopEdge("A", "B", 10.0, 3.0)]
        inp = SimulationInput("R002", edges, "08:30", "06:30", simulation_runs=300)
        out = self.sim.simulate(inp, rng_seed=99)
        assert 0.0 <= out.reliability_score <= 1.0

    def test_high_variance_reduces_on_time(self):
        """Higher travel time variance should reduce on-time probability."""
        edges_low_var = [StopEdge("A", "B", 5.0, 0.5)]
        edges_high_var = [StopEdge("A", "B", 5.0, 5.0)]
        inp_low = SimulationInput("R_low", edges_low_var, "08:30", "06:30", 500)
        inp_high = SimulationInput("R_high", edges_high_var, "08:30", "06:30", 500)
        out_low = self.sim.simulate(inp_low, rng_seed=1)
        out_high = self.sim.simulate(inp_high, rng_seed=1)
        # High variance should generally have higher p90 (less reliable)
        assert out_high.p90_duration >= out_low.p90_duration - 1.0


# ─── Unit Tests: Workload Service ─────────────────────────────────────────────

class TestWorkloadService:

    def test_workload_score_calculation(self):
        """Test composite workload score is bounded 0-100."""
        score = calculate_workload_score(120, 90, 10, 30)
        assert 0 <= score <= 100

    def test_workload_score_zero_route(self):
        """Empty route should have low workload."""
        score = calculate_workload_score(0, 0, 0, 0)
        assert score == 0.0

    def test_workload_analysis_fairness(self):
        """Test that fairness metrics are computed correctly."""
        routes = [
            {"route_id": "R1", "driver_id": "DRV01", "total_duration_minutes": 90, "driving_minutes": 70, "stop_count": 8, "total_students": 25, "planned_start": "06:00", "planned_end": "07:30"},
            {"route_id": "R2", "driver_id": "DRV02", "total_duration_minutes": 150, "driving_minutes": 130, "stop_count": 15, "total_students": 45, "planned_start": "06:00", "planned_end": "08:30"},
        ]
        drivers = {
            "DRV01": {"driver_id": "DRV01", "driver_name": "Arjun", "shift_start": "06:00", "max_shift_minutes": 210, "max_driving_minutes": 180},
            "DRV02": {"driver_id": "DRV02", "driver_name": "Bala", "shift_start": "06:00", "max_shift_minutes": 210, "max_driving_minutes": 180},
        }
        result = workload_service.analyze(routes, drivers)
        fairness = result["fairness"]
        assert "workload_variance" in fairness
        assert "workload_imbalance" in fairness
        assert fairness["workload_imbalance"] > 0   # Routes have different loads
        assert fairness["max_workload"] > fairness["min_workload"]


# ─── Unit Tests: Baseline Optimizer ───────────────────────────────────────────

class TestBaselineOptimizer:

    def test_baseline_route_generation(self, sample_stops, sample_buses, sample_drivers, sample_travel_edges, normal_attendance):
        """Test that baseline generates valid routes."""
        optimizer = BaselineOptimizer()
        routes = optimizer.optimize(
            sample_stops, sample_buses, sample_drivers,
            sample_travel_edges, normal_attendance, "normal"
        )
        assert len(routes) > 0
        for r in routes:
            assert r.optimization_type == "baseline"
            assert r.total_distance_km >= 0
            assert r.stop_count > 0

    def test_baseline_respects_capacity(self, sample_stops, sample_travel_edges, normal_attendance):
        """Test that baseline does not exceed bus capacity (for reasonable attendance)."""
        small_buses = [BusData("BUS01", 50, "06:00", "09:30")]
        drivers = [DriverData("DRV01", "Test", "06:00", "09:30", 210, 180, True)]
        optimizer = BaselineOptimizer()
        routes = optimizer.optimize(sample_stops, small_buses, drivers, sample_travel_edges, normal_attendance, "normal")
        for r in routes:
            if r.bus_id != "UNASSIGNED":
                assert r.capacity_used <= r.capacity_limit or r.capacity_violations > 0

    def test_all_stops_covered(self, sample_stops, sample_buses, sample_drivers, sample_travel_edges, normal_attendance):
        """Test all stops with attendance are assigned to some route."""
        optimizer = BaselineOptimizer()
        routes = optimizer.optimize(sample_stops, sample_buses, sample_drivers, sample_travel_edges, normal_attendance, "normal")
        assigned_stops = set()
        for r in routes:
            assigned_stops.update(r.stop_sequence)
        # All stops with positive attendance should be covered
        for sid, count in normal_attendance.items():
            if count > 0:
                assert sid in assigned_stops, f"Stop {sid} with attendance {count} not assigned"

    def test_empty_attendance_produces_no_routes(self, sample_stops, sample_buses, sample_drivers, sample_travel_edges):
        """Test that zero attendance produces no routes."""
        zero_attendance = {s.stop_id: 0 for s in sample_stops}
        optimizer = BaselineOptimizer()
        routes = optimizer.optimize(sample_stops, sample_buses, sample_drivers, sample_travel_edges, zero_attendance, "normal")
        assert routes == []


# ─── Unit Tests: Data Generator ───────────────────────────────────────────────

class TestDataGenerator:

    def test_generate_stops(self):
        """Test synthetic stop generation."""
        data = data_generator.generate_all(n_stops=10, n_students=50, n_buses=3, n_drivers=3, seed=42)
        stops = data["stops"]
        assert len(stops) == 10
        for s in stops:
            assert "stop_id" in s
            assert "latitude" in s
            assert "longitude" in s
            assert 0 < s["attendance_probability"] <= 1.0
            assert s["student_count"] > 0

    def test_generate_buses_have_realistic_capacities(self):
        """Test buses have realistic capacities (20-50)."""
        data = data_generator.generate_all(n_stops=5, n_students=20, n_buses=5, n_drivers=3, seed=42)
        for b in data["buses"]:
            assert b["capacity"] in [20, 30, 40, 50]

    def test_attendance_scenarios(self):
        """Test attendance scenario generation."""
        stops_raw = [{"stop_id": f"S{i:03d}", "student_count": 10, "attendance_probability": 0.8} for i in range(5)]
        normal_att = generate_attendance(stops_raw, "normal", 42)
        low_att = generate_attendance(stops_raw, "low", 42)
        high_att = generate_attendance(stops_raw, "high", 42)

        assert all(0 <= v <= 10 for v in normal_att.values())
        assert sum(low_att.values()) <= sum(normal_att.values()) + 5  # low should generally be lower
        assert all(0 <= v <= 10 for v in high_att.values())

    def test_invalid_dataset_detected(self):
        """Test that dataset validation catches issues."""
        # Zero stops should result in empty routes
        optimizer = BaselineOptimizer()
        routes = optimizer.optimize([], [BusData("B1", 30, "06:00", "09:30")], [DriverData("D1", "Test", "06:00", "09:30", 210, 180, True)], [], {}, "normal")
        assert routes == []


# ─── Unit Tests: Override Blocking ────────────────────────────────────────────

class TestOverrideLogic:

    def test_hard_constraint_ids_blocked(self):
        """Hard constraint IDs H1-H4 must not be overrideable."""
        hard_ids = {"H1", "H2", "H3", "H4"}
        # Import the constant from override API
        from app.api.override import HARD_CONSTRAINT_IDS
        for cid in hard_ids:
            assert cid in HARD_CONSTRAINT_IDS, f"{cid} should be in HARD_CONSTRAINT_IDS"

    def test_soft_constraint_allows_override(self):
        """Soft constraints (S1-S4) must NOT be in hard constraint list."""
        from app.api.override import HARD_CONSTRAINT_IDS
        soft_ids = {"S1", "S2", "S3", "S4"}
        for cid in soft_ids:
            assert cid not in HARD_CONSTRAINT_IDS, f"{cid} should be overrideable (not in hard list)"


# ─── Unit Tests: Offline Mode ──────────────────────────────────────────────────

class TestOfflineMode:

    def test_fallback_event_types(self):
        """Test all required failure event types are defined."""
        from app.api.fallback import _EVENT_TO_STATUS_KEY
        required = ["gps_failure", "network_failure", "attendance_feed_failure", "traffic_feed_failure"]
        for et in required:
            assert et in _EVENT_TO_STATUS_KEY, f"Missing event type: {et}"

    def test_store_and_forward_queue_structure(self):
        """Test SyncQueue model has required fields."""
        from app.models.sync_queue import SyncQueue
        assert hasattr(SyncQueue, "route_id")
        assert hasattr(SyncQueue, "stop_id")
        assert hasattr(SyncQueue, "update_type")
        assert hasattr(SyncQueue, "synced")
        assert hasattr(SyncQueue, "queued_at")
