# School-Bus Route Planner — End-to-End Demo Script & Walkthrough

This demo script walks through the entire live presentation of the **Multi-Objective School-Bus Route Planner for Variable Student Attendance**.

---

## 1. Credentials & Quick Access

* **Application URL**: `http://localhost:5173`
* **API Documentation**: `http://localhost:8000/docs`
* **Planner / Admin Login**:
  * **Username**: `admin`
  * **Password**: `admin123`
* **Driver Login**:
  * **Username**: `driver`
  * **Password**: `driver123`

---

## 2. Walkthrough Flow

### Step 1: Login & Role Selection
1. Navigate to `http://localhost:5173/login`.
2. Click **"Planner / Admin Demo"** to pre-fill credentials (`admin` / `admin123`).
3. Click **"Sign In"**. You are redirected to the Dashboard.

### Step 2: System Health & KPI Dashboard
1. Review the dashboard top KPI cards:
   * Total Stops (75)
   * Registered Students (350)
   * Fleet Size (10 buses)
   * Active Drivers (10 drivers)
2. View the **System Status banner** (Operational / All services green).
3. Check the **Daily Route Efficiency & Attendance chart**.

### Step 3: Dataset Generation & Preview
1. Navigate to **Data Management** (`/data`).
2. Notice the pre-loaded 75 stops across Chennai metro area with realistic coordinates.
3. Switch between tabs: **Stops**, **Students**, **Buses**, **Drivers**, and **Travel Times**.
4. Test the **"Generate Fresh Synthetic Data"** button with a custom seed or size to demonstrate stochastic data generation.

### Step 4: Baseline Clarke-Wright & Distance Optimization
1. Navigate to **Optimization Engine** (`/optimization`).
2. Run the **Baseline Optimizer** (Clarke-Wright Savings / Pure Distance VRP).
3. Review the execution metrics:
   * Total Distance traveled
   * Maximum Driver Workload
   * Estimated On-Time Arrival Probability (typically ~72% under baseline due to ignoring traffic variance)

### Step 5: Multi-Objective Route Optimization
1. Adjust the objective weight sliders:
   * **Travel Distance Weight ($w_1$)**: default 0.35
   * **Time-Window Compliance ($w_2$)**: default 0.30
   * **Reliability Buffer ($w_3$)**: default 0.20
   * **Driver Workload Fairness ($w_4$)**: default 0.15
2. Click **"Run Multi-Objective Optimization"**.
3. Watch the optimization solve with OR-Tools VRPTW solver incorporating time windows, capacity limits, and variance penalty buffers.

### Step 6: Route Map & Visual Dispatch
1. Navigate to **Route Map** (`/routes`).
2. Explore the interactive **Leaflet map**:
   * Color-coded route trajectories for each bus.
   * School depot marker with central coordinates.
   * Interactive stop pins showing student pickup counts and arrival time windows.
3. Select an individual bus route from the sidebar to inspect its turn-by-turn stop sequence and cumulative load.

### Step 7: Baseline vs. Optimized Comparison
1. Navigate to **Comparison** (`/comparison`).
2. Review the side-by-side comparison table:
   * **Total Distance**: Baseline vs Multi-Objective
   * **P95 Arrival Time**: Baseline vs Multi-Objective
   * **Driver Workload Gini Index / Variance**: Significant improvement in fairness
   * **On-Time Reliability**: Baseline (~72%) vs Multi-Objective (>92%)
3. Review the **Trade-Off Radar Chart** and **Pareto Frontier chart**.

### Step 8: Monte Carlo Reliability & Stress Testing
1. Navigate to **Reliability Simulation** (`/reliability`).
2. Run a 500-trial **Monte Carlo Simulation** using lognormal travel times.
3. Inspect:
   * Arrival time percentiles (P50, P90, P95).
   * Distribution histogram showing arrival variances under bad weather/congestion scenarios.
   * Probability of meeting the 08:30 AM hard school bell time.

### Step 9: Driver Workload & Shift Fairness
1. Navigate to **Workload Fairness** (`/workload`).
2. Inspect individual driver shift durations, total route distance, and student passenger loads.
3. Review the **Jain's Fairness Index** metric and max-to-min ratio showing equitable distribution among drivers.

### Step 10: Failure Modes & Offline-First Operation
1. Navigate to **Fallback & Resilience** (`/fallback`).
2. Click **"Simulate GPS / Network Loss"**.
3. Observe the system switch to **Offline Mode**:
   * Driver UI continues operating using local storage cached manifests.
   * Stop check-ins and attendance updates queue into the **Store-and-Forward Queue**.
4. Click **"Restore Connection & Sync Queue"**.
5. Observe queued check-ins replay and synchronize with the central backend with zero data loss.

### Step 11: Stakeholder Validation & Feedback
1. Navigate to **Stakeholder Validation** (`/validation`).
2. Fill out validation reviews across stakeholder roles:
   * **School Administrator** (Safety & Bell-time compliance)
   * **Fleet Manager** (Vehicle utilization & fuel savings)
   * **Driver Representative** (Shift equality & fatigue prevention)
   * **Parent** (Pickup predictability & ride duration)
3. Submit ratings and view the aggregate **Readiness Score**.

### Step 12: Comprehensive Evaluation Report Export
1. Navigate to **Reports & Export** (`/reports`).
2. View the complete executive evaluation report containing:
   * Research questions answered
   * Benchmark tables
   * Statistical significance tests ($p < 0.05$)
   * Recommendations for production deployment
3. Click **"Export as PDF"** or **"Export as HTML"** to generate an official stakeholder report.

---

## 3. Automated Test Verification

Run all unit and integration test suites:
```bash
cd backend
python -m pytest tests/test_all.py -v
```
Expected output: **24 passed** in under 3 seconds.
