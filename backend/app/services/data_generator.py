"""
Synthetic Data Generator for School-Bus Route Planner.

Generates a realistic school-bus network for the Chennai metropolitan area
(fictional stops, plausible coordinates, realistic travel times).

Dataset:
- 75 stops across 5 zones
- 350 students
- 10 buses (20–50 capacity)
- 10 drivers with shift limits
- Travel-time matrix with lognormal distributions
"""
import uuid
import math
import random
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime

# ─── Realistic stop names (Chennai metro area - fictional but plausible) ──────
STOP_NAMES = [
    "Anna Nagar East Gate", "Anna Nagar Tower Park", "Vadapalani Signal",
    "Arumbakkam Metro", "Koyambedu Bus Stand", "CMBT West Entrance",
    "Porur Flyover", "Porur Lake Road", "Ramapuram Circle",
    "Mugalivakkam Bridge", "Gerugambakkam Cross", "Valasaravakkam Main",
    "Virugambakkam Park", "Saligramam Junction", "Aminjikarai North",
    "Nungambakkam High Road", "Khader Nawaz Khan Road", "Chetpet Lake Front",
    "Kilpauk Medical College", "Perambur Barracks", "Kolathur Market",
    "Villivakkam Railway Gate", "Ambattur OT", "Ambattur Industrial Estate",
    "Padi Junction", "Thirumangalam Metro", "Mogappair East",
    "Mogappair West", "Maduravoyal Circle", "Manappakkam Bypass",
    "Pallavaram EB Colony", "Chrompet Signal", "Tambaram West",
    "St Thomas Mount", "Meenambakkam Flyover", "Alandur Metro",
    "Guindy Industrial Estate", "Guindy Anna University Gate",
    "Saidapet Court Road", "Mambalam West", "T Nagar West",
    "Pondy Bazaar North", "Kodambakkam Studio Lane", "Ashok Nagar 4th Ave",
    "K K Nagar Market", "Madipakkam Main Road", "Velachery MRTS",
    "Velachery Main Road", "Pallikaranai Marsh Road", "Sholinganallur Signal",
    "Perungudi IT Park", "Thoraipakkam 100 Feet Road", "Kandanchavadi Bus Stop",
    "Navalur Toll Gate", "Siruseri SIPCOT", "Kelambakkam Junction",
    "Adyar Depot", "Adyar Junction", "Besant Nagar Beach Road",
    "Thiruvanmiyur 5th Ave", "ECR Kottivakkam", "Palavakkam Beach",
    "Neelankarai Signal", "Injambakkam Road", "Kovalam Junction",
    "Mylapore Tank", "Luz Corner", "Royapettah Hospital Road",
    "Triplicane Market", "Mannady Junction", "George Town Post Office",
    "Washermanpet Junction", "Tondiarpet North", "Ennore Expressway",
    "Madhavaram Milk Colony", "Redhills Road", "Puzhal Camp Road",
]

# ─── GPS bounding box — Chennai metro (approx) ────────────────────────────────
LAT_MIN, LAT_MAX = 12.85, 13.20
LON_MIN, LON_MAX = 80.10, 80.28

# ─── Zone definitions ─────────────────────────────────────────────────────────
ZONES = {
    "A": {"name": "North Chennai", "lat": (13.05, 13.20), "lon": (80.20, 80.28)},
    "B": {"name": "West Chennai",  "lat": (13.00, 13.10), "lon": (80.10, 80.18)},
    "C": {"name": "Central",       "lat": (13.02, 13.08), "lon": (80.22, 80.28)},
    "D": {"name": "South Chennai", "lat": (12.85, 13.00), "lon": (80.20, 80.28)},
    "E": {"name": "Southwest",     "lat": (12.90, 13.02), "lon": (80.10, 80.20)},
}

# ─── Time windows (HH:MM) ─────────────────────────────────────────────────────
# School starts at 08:45 → buses must arrive at school by 08:30
# Pickup windows vary by zone (farther zones start earlier)
ZONE_PICKUP_WINDOWS = {
    "A": ("06:15", "07:00"),
    "B": ("06:30", "07:15"),
    "C": ("07:00", "07:45"),
    "D": ("07:15", "08:00"),
    "E": ("06:45", "07:30"),
}

DRIVER_NAMES = [
    "Arjun Krishnamurthy", "Bala Subramaniam", "Chandran Pillai",
    "Deepak Venkatesh", "Eswaran Natarajan", "Farook Rahman",
    "Ganesan Murugan", "Hari Prasad", "Ilayaraja Selvam", "Jayakumar Ravi",
]


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Compute distance in km between two GPS points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _lognormal_params(mean: float, std: float):
    """Compute (mu, sigma) for lognormal dist with given mean and std."""
    if mean <= 0 or std <= 0:
        return math.log(max(mean, 0.5)), 0.1
    variance = std ** 2
    mu = math.log(mean ** 2 / math.sqrt(variance + mean ** 2))
    sigma = math.sqrt(math.log(1 + variance / mean ** 2))
    return round(mu, 4), round(sigma, 4)


def generate_stops(n: int = 75, seed: int = 42) -> List[Dict]:
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)
    stops = []
    zone_keys = list(ZONES.keys())

    for i, name in enumerate(STOP_NAMES[:n]):
        zone = zone_keys[i % len(zone_keys)]
        z = ZONES[zone]
        lat = rng.uniform(*z["lat"])
        lon = rng.uniform(*z["lon"])
        student_count = rng.randint(4, 18)
        attend_prob = round(rng.uniform(0.55, 0.98), 2)
        pickup_win = ZONE_PICKUP_WINDOWS[zone]
        delay_prob = round(rng.uniform(0.02, 0.18), 3)
        svc_time = round(rng.uniform(1.5, 4.0), 1)
        priority = rng.choice([1, 1, 1, 2, 2, 3])

        stops.append({
            "stop_id": f"S{i+1:03d}",
            "stop_name": name,
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "student_count": student_count,
            "attendance_probability": attend_prob,
            "pickup_window_start": pickup_win[0],
            "pickup_window_end": pickup_win[1],
            "dropoff_window_start": "13:30",
            "dropoff_window_end": "14:30",
            "service_time_minutes": svc_time,
            "priority": priority,
            "historical_delay_probability": delay_prob,
            "zone": zone,
            "is_active": True,
        })
    return stops


def generate_students(stops: List[Dict], total: int = 350, seed: int = 42) -> List[Dict]:
    rng = random.Random(seed)
    students = []
    sid = 1

    # Distribute students proportionally to stop student_count
    total_raw = sum(s["student_count"] for s in stops)
    first_names = [
        "Aarav", "Aditi", "Arjun", "Bhavya", "Chetan", "Deepa", "Dhruv",
        "Esha", "Farida", "Gautam", "Hema", "Ishaan", "Jaya", "Karan",
        "Lakshmi", "Manish", "Nandini", "Om", "Priya", "Rahul", "Sanjana",
        "Tarun", "Uma", "Vikas", "Yamini", "Zara", "Anil", "Brinda", "Chitra",
    ]
    last_names = [
        "Sharma", "Kumar", "Patel", "Singh", "Verma", "Gupta", "Nair",
        "Pillai", "Rao", "Rajan", "Menon", "Iyer", "Krishnan", "Reddy",
        "Chandra", "Bose", "Das", "Sen", "Mukherjee", "Joshi",
    ]

    for stop in stops:
        n_students = stop["student_count"]
        for j in range(n_students):
            if sid > total:
                break
            attend_p = round(rng.gauss(stop["attendance_probability"], 0.08), 2)
            attend_p = max(0.3, min(1.0, attend_p))
            name = f"{rng.choice(first_names)} {rng.choice(last_names)}"
            students.append({
                "student_id": f"STU{sid:04d}",
                "stop_id": stop["stop_id"],
                "attendance_probability": attend_p,
                "weekday": "all",
                "expected_attendance": attend_p,
                "name": name,
                "grade": rng.randint(1, 10),
                "is_active": True,
            })
            sid += 1
        if sid > total:
            break
    return students


def generate_buses(n: int = 10, seed: int = 42) -> List[Dict]:
    rng = random.Random(seed)
    capacities = [20, 30, 30, 40, 40, 40, 50, 50, 50, 50]
    rng.shuffle(capacities)
    buses = []
    for i in range(n):
        buses.append({
            "bus_id": f"BUS{i+1:02d}",
            "registration": f"TN{rng.randint(1,99):02d} AB {rng.randint(1000,9999)}",
            "capacity": capacities[i % len(capacities)],
            "available_start_time": "06:00",
            "available_end_time": "09:30",
            "fuel_type": rng.choice(["diesel", "diesel", "cng", "electric"]),
            "is_active": True,
            "current_driver_id": None,
            "notes": "",
        })
    return buses


def generate_drivers(n: int = 10, seed: int = 42) -> List[Dict]:
    rng = random.Random(seed)
    drivers = []
    phones = [f"+91 98{rng.randint(10000000, 99999999)}" for _ in range(n)]
    for i in range(n):
        shift_start = rng.choice(["05:45", "06:00", "06:15", "06:30"])
        drivers.append({
            "driver_id": f"DRV{i+1:02d}",
            "driver_name": DRIVER_NAMES[i % len(DRIVER_NAMES)],
            "shift_start": shift_start,
            "shift_end": "09:30",
            "max_shift_minutes": rng.choice([210, 210, 195, 225]),
            "max_driving_minutes": rng.choice([180, 180, 165, 195]),
            "break_requirement": 30,
            "availability": True,
            "license_type": "Heavy",
            "phone": phones[i],
            "years_experience": rng.randint(2, 20),
            "workload_score": 0.0,
        })
    return drivers


def generate_travel_times(stops: List[Dict], seed: int = 42) -> List[Dict]:
    """
    Generate realistic travel times between consecutive-zone stops.
    Uses haversine distance + realistic speed assumptions + lognormal noise.
    Only generates pairs within ~15 km (not all N² pairs for 75 stops).
    """
    rng = random.Random(seed)
    travel_times = []
    stop_index = {s["stop_id"]: s for s in stops}
    stop_ids = [s["stop_id"] for s in stops]

    # Generate travel times for all pairs within the same or adjacent zones
    # (limits the matrix to a manageable size)
    zone_adjacency = {
        "A": ["A", "B", "C"],
        "B": ["A", "B", "C", "E"],
        "C": ["A", "B", "C", "D"],
        "D": ["C", "D", "E"],
        "E": ["B", "D", "E"],
    }

    seen = set()
    for s1 in stops:
        adj_zones = zone_adjacency.get(s1["zone"], list(ZONES.keys()))
        for s2 in stops:
            if s1["stop_id"] == s2["stop_id"]:
                continue
            if s2["zone"] not in adj_zones:
                continue
            key = tuple(sorted([s1["stop_id"], s2["stop_id"]]))
            if key in seen:
                continue
            seen.add(key)

            dist = _haversine_km(s1["latitude"], s1["longitude"],
                                  s2["latitude"], s2["longitude"])
            if dist > 18.0:   # skip very distant pairs
                continue

            # Average speed 25–45 km/h depending on traffic
            base_speed = rng.uniform(22, 42)
            mean_tt = (dist / base_speed) * 60  # minutes
            # Coefficient of variation 15–35%
            cv = rng.uniform(0.15, 0.35)
            std_tt = mean_tt * cv

            # Traffic condition
            if dist > 10:
                traffic = rng.choice(["heavy", "normal", "normal"])
            else:
                traffic = rng.choice(["light", "normal", "normal", "heavy"])

            # Traffic multiplier
            traffic_mult = {"light": 0.85, "normal": 1.0, "heavy": 1.35}[traffic]
            mean_tt *= traffic_mult
            std_tt *= traffic_mult

            mu, sigma = _lognormal_params(mean_tt, std_tt)

            # Compute percentiles analytically
            p50 = round(math.exp(mu), 2)
            p90 = round(math.exp(mu + 1.282 * sigma), 2)
            p95 = round(math.exp(mu + 1.645 * sigma), 2)

            tt_id = f"{s1['stop_id']}_{s2['stop_id']}"
            travel_times.append({
                "id": tt_id,
                "from_stop": s1["stop_id"],
                "to_stop": s2["stop_id"],
                "distance_km": round(dist, 3),
                "mean_travel_time": round(mean_tt, 2),
                "std_travel_time": round(std_tt, 2),
                "p50_time": p50,
                "p90_time": p90,
                "p95_time": p95,
                "traffic_condition": traffic,
                "lognormal_mu": mu,
                "lognormal_sigma": sigma,
            })
            # Add reverse direction (slightly different traffic)
            rev_tt = mean_tt * rng.uniform(0.92, 1.08)
            rev_std = std_tt * rng.uniform(0.90, 1.10)
            rev_mu, rev_sigma = _lognormal_params(rev_tt, rev_std)
            rev_id = f"{s2['stop_id']}_{s1['stop_id']}"
            travel_times.append({
                "id": rev_id,
                "from_stop": s2["stop_id"],
                "to_stop": s1["stop_id"],
                "distance_km": round(dist, 3),
                "mean_travel_time": round(rev_tt, 2),
                "std_travel_time": round(rev_std, 2),
                "p50_time": round(math.exp(rev_mu), 2),
                "p90_time": round(math.exp(rev_mu + 1.282 * rev_sigma), 2),
                "p95_time": round(math.exp(rev_mu + 1.645 * rev_sigma), 2),
                "traffic_condition": traffic,
                "lognormal_mu": rev_mu,
                "lognormal_sigma": rev_sigma,
            })

    return travel_times


def generate_attendance(
    stops: List[Dict],
    scenario: str = "normal",
    seed: int = 42,
) -> Dict[str, int]:
    """
    Generate actual daily attendance for each stop based on scenario.
    Returns {stop_id: realized_student_count}.
    """
    rng = np.random.default_rng(seed)
    attendance = {}

    scenario_multipliers = {
        "normal": 1.0,
        "low": 0.6,
        "high": 1.0,   # capped by student_count
        "random": None,  # fully random
        "custom": 0.8,
    }

    for stop in stops:
        n = stop["student_count"]
        p = stop["attendance_probability"]

        if scenario == "random":
            # Each student independently attends with their probability
            realized = int(rng.binomial(n, p))
        elif scenario == "low":
            realized = int(rng.binomial(n, max(0.1, p * 0.6)))
        elif scenario == "high":
            realized = int(rng.binomial(n, min(1.0, p * 1.15)))
        else:  # normal
            realized = int(rng.binomial(n, p))

        attendance[stop["stop_id"]] = min(realized, n)

    return attendance


class DataGenerator:
    """High-level data generation service."""

    def generate_all(
        self,
        n_stops: int = 75,
        n_students: int = 350,
        n_buses: int = 10,
        n_drivers: int = 10,
        seed: int = 42,
    ) -> Dict:
        stops = generate_stops(n_stops, seed)
        students = generate_students(stops, n_students, seed)
        buses = generate_buses(n_buses, seed)
        drivers = generate_drivers(n_drivers, seed)
        travel_times = generate_travel_times(stops, seed)

        return {
            "stops": stops,
            "students": students,
            "buses": buses,
            "drivers": drivers,
            "travel_times": travel_times,
            "metadata": {
                "n_stops": len(stops),
                "n_students": len(students),
                "n_buses": len(buses),
                "n_drivers": len(drivers),
                "n_travel_time_pairs": len(travel_times),
                "seed": seed,
                "generated_at": datetime.utcnow().isoformat(),
            }
        }


# Global singleton
data_generator = DataGenerator()
