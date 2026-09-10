"""
Monte Carlo Reliability Simulator.

Simulates travel-time uncertainty using lognormal distributions to compute:
- P50, P90, P95 route durations
- On-time probability
- Reliability score
"""
import math
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class StopEdge:
    from_stop: str
    to_stop: str
    mean_travel_time: float   # minutes
    std_travel_time: float    # minutes
    service_time: float = 2.0


@dataclass
class SimulationInput:
    route_id: str
    edges: List[StopEdge]
    required_completion_hhmm: str   # "08:30"
    route_start_hhmm: str           # "06:30"
    simulation_runs: int = 500


@dataclass
class SimulationOutput:
    route_id: str
    simulation_runs: int
    expected_duration: float
    p50_duration: float
    p90_duration: float
    p95_duration: float
    min_duration: float
    max_duration: float
    std_duration: float
    late_probability: float
    on_time_probability: float
    reliability_score: float
    scenarios_on_time: int
    time_window: str
    duration_samples: List[float]   # for histogram


def _lognormal_params(mean: float, std: float) -> Tuple[float, float]:
    """Compute mu and sigma of the underlying normal dist for a lognormal."""
    if mean <= 0 or std <= 0:
        return math.log(max(mean, 0.5)), 0.1
    variance = std ** 2
    mu = math.log(mean ** 2 / math.sqrt(variance + mean ** 2))
    sigma = math.sqrt(math.log(1 + variance / mean ** 2))
    return mu, sigma


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


class MonteCarloSimulator:
    """
    Runs Monte Carlo simulations on a route using lognormal travel-time distributions.
    """

    def simulate(self, inp: SimulationInput, rng_seed: Optional[int] = None) -> SimulationOutput:
        rng = np.random.default_rng(rng_seed)
        required_minutes = _hhmm_to_minutes(inp.required_completion_hhmm)
        start_minutes = _hhmm_to_minutes(inp.route_start_hhmm)

        # Pre-compute lognormal params for each edge
        params = []
        for edge in inp.edges:
            mu, sigma = _lognormal_params(edge.mean_travel_time, edge.std_travel_time)
            params.append((mu, sigma, edge.service_time))

        # Run simulations
        durations = np.zeros(inp.simulation_runs)
        for i in range(inp.simulation_runs):
            total = 0.0
            for mu, sigma, svc in params:
                travel = rng.lognormal(mu, sigma)
                # Clip to reasonable bounds (0.5× to 3× mean)
                travel = np.clip(travel, params[0][0] * 0.5, max(travel, 0.5))
                total += travel + svc
            durations[i] = total

        # Statistics
        p50 = float(np.percentile(durations, 50))
        p90 = float(np.percentile(durations, 90))
        p95 = float(np.percentile(durations, 95))
        expected = float(np.mean(durations))
        std = float(np.std(durations))
        min_d = float(np.min(durations))
        max_d = float(np.max(durations))

        # On-time = route finishes before required completion time
        available_window = required_minutes - start_minutes
        on_time = int(np.sum(durations <= available_window))
        on_time_prob = on_time / inp.simulation_runs
        late_prob = 1.0 - on_time_prob

        # Reliability score: weighted mix of on-time prob and margin
        margin = (available_window - p90) / max(available_window, 1)
        reliability_score = 0.7 * on_time_prob + 0.3 * max(0.0, min(1.0, 0.5 + margin))

        return SimulationOutput(
            route_id=inp.route_id,
            simulation_runs=inp.simulation_runs,
            expected_duration=round(expected, 2),
            p50_duration=round(p50, 2),
            p90_duration=round(p90, 2),
            p95_duration=round(p95, 2),
            min_duration=round(min_d, 2),
            max_duration=round(max_d, 2),
            std_duration=round(std, 2),
            late_probability=round(late_prob, 4),
            on_time_probability=round(on_time_prob, 4),
            reliability_score=round(reliability_score, 4),
            scenarios_on_time=on_time,
            time_window=inp.required_completion_hhmm,
            duration_samples=durations.tolist()[:100],  # send first 100 for histogram
        )

    def batch_simulate(self, inputs: List[SimulationInput]) -> List[SimulationOutput]:
        return [self.simulate(inp) for inp in inputs]


# Global singleton
simulator = MonteCarloSimulator()
