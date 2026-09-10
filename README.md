# Multi-Objective School-Bus Route Planner for Variable Student Attendance

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.111-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_18_%2B_Vite-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![OR-Tools](https://img.shields.io/badge/Optimization-Google_OR--Tools-4285F4.svg?logo=google&logoColor=white)](https://developers.google.com/optimization)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind_CSS-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Tests](https://img.shields.io/badge/Tests-24_Passed-success.svg)](#testing)

An end-to-end, production-ready full-stack prototype that solves the **School-Bus Routing Problem with Time Windows (VRPTW)** under **variable student attendance**, stochastic traffic distributions, and driver workload constraints.

---

## Architecture Overview

```
school-bus-route-planner/
├── frontend/                     # React 18 + Vite + TypeScript + Tailwind CSS
│   ├── src/
│   │   ├── pages/                # 13 Complete interactive pages
│   │   ├── components/           # KPI cards, Leaflet map, charts, modals
│   │   ├── api/                  # Axios HTTP client & API hooks
│   │   └── store/                # Zustand client state management
│   └── package.json
├── backend/                      # Python 3.11+ / FastAPI / SQLAlchemy / OR-Tools
│   ├── app/
│   │   ├── api/                  # 13 REST API routers
│   │   ├── models/               # SQLAlchemy ORM relational models
│   │   ├── optimization/         # Clarke-Wright baseline & Multi-Objective OR-Tools
│   │   ├── simulation/           # 500-iteration Monte Carlo reliability simulator
│   │   ├── constraints/          # Hard, soft, and override validation engine
│   │   ├── services/             # Workload fairness & data generator services
│   │   ├── fallback/             # Offline queue & network fault resilience
│   │   └── reports/              # Executive report generator (HTML + PDF)
│   ├── tests/                    # 24 Pytest unit & integration test suite
│   ├── requirements.txt
│   └── main.py
├── data/
│   ├── raw/                      # Ingested datasets
│   ├── cleaned/                  # Validated and normalized tables
│   └── synthetic/                # 75 stops, 350 students, 10 buses, 10 drivers
├── scripts/
│   └── generate_data.py          # Standalone CLI data generator
├── docs/
│   └── DEMO_SCRIPT.md            # Complete 12-step presentation script
├── docker-compose.yml            # Container orchestration
└── run.bat                       # One-click Windows startup script
```

---

## Core Capabilities

1. **Multi-Objective Optimization Engine**:
   * Blends four competing objectives: **Travel Distance Minimization**, **Time-Window Compliance**, **Reliability Buffer Maximization**, and **Driver Workload Fairness**.
   * Solves using **Google OR-Tools VRPTW** with dimension capacity and cumulative slack variables.

2. **Benchmark Comparison vs. Classical Baseline**:
   * Compares multi-objective outcomes directly against a traditional **Clarke-Wright Savings / Distance-Only VRP** baseline.
   * Visualizes trade-offs via interactive radar charts and Pareto frontier graphs.

3. **Stochastic Reliability & Monte Carlo Simulation**:
   * 500-run Monte Carlo simulations modeling non-Gaussian (lognormal) travel-time uncertainty.
   * Produces P50, P90, and P95 arrival percentiles to guarantee on-time arrival before the 08:30 AM bell.

4. **Driver Shift Equity & Workload Balancing**:
   * Evaluates driver shift equity using **Jain's Fairness Index** and variance penalties, avoiding driver burnout.

5. **Fault-Tolerant Offline Operation**:
   * Resilient to GPS dropouts, cellular dead-zones, and server disconnects.
   * Browser-cached manifests and **Store-and-Forward Sync Queue** ensure zero lost pickup events during outages.

6. **Interactive Spatial Map & Live Dispatch**:
   * Dynamic **Leaflet** GIS map rendering colored bus trajectories, depot locations, and stop-by-stop passenger loads.

---

## Quick Start Guide

### Prerequisites
* **Python 3.10+**
* **Node.js 18+**

### Option 1: One-Click Windows Launch
Double-click `run.bat` or execute in PowerShell:
```cmd
run.bat
```

### Option 2: Manual Terminal Startup

#### 1. Setup & Launch Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
* Backend API: [http://localhost:8000](http://localhost:8000)
* Interactive Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

#### 2. Setup & Launch Frontend
```bash
cd frontend
npm install
npm run dev
```
* Application UI: [http://localhost:5173](http://localhost:5173)

---

## Demo Credentials

| Role | Username | Password | Capabilities |
|---|---|---|---|
| **Transportation Planner / Admin** | `admin` | `admin123` | Full access: data gen, optimization, overrides, reports |
| **Bus Driver** | `driver` | `driver123` | Manifest view, stop check-ins, offline mode |

---

## Testing

Run the full automated test suite:
```bash
cd backend
python -m pytest tests/test_all.py -v
```
**Results**: 24 tests passing across constraint checks, baseline optimizer, OR-Tools, Monte Carlo simulation, driver fairness, and offline queues.

---

## Presentation & Walkthrough
For step-by-step guidance on running a live demonstration of all features, refer to [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md).
