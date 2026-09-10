"""
Multi-Objective School-Bus Route Planner
FastAPI Backend Entry Point
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.api import auth, dashboard, data, routes, optimization, workload, comparison, override, fallback, experiments, validation, reports, simulation


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database on startup."""
    init_db()
    yield


app = FastAPI(
    title="School-Bus Route Planner API",
    description="Multi-Objective School-Bus Route Planner with reliability simulation, driver workload balancing, and offline-first operation.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount reports directory for static file serving
os.makedirs("reports", exist_ok=True)
app.mount("/reports", StaticFiles(directory="reports"), name="reports")

# Register all API routers
app.include_router(auth.router,         prefix="/api/auth",         tags=["auth"])
app.include_router(dashboard.router,    prefix="/api/dashboard",    tags=["dashboard"])
app.include_router(data.router,         prefix="/api/data",         tags=["data"])
app.include_router(routes.router,       prefix="/api/routes",       tags=["routes"])
app.include_router(optimization.router, prefix="/api/optimization", tags=["optimization"])
app.include_router(simulation.router,   prefix="/api/simulation",   tags=["simulation"])
app.include_router(workload.router,     prefix="/api/workload",     tags=["workload"])
app.include_router(comparison.router,   prefix="/api/comparison",   tags=["comparison"])
app.include_router(override.router,     prefix="/api/override",     tags=["override"])
app.include_router(fallback.router,     prefix="/api/fallback",     tags=["fallback"])
app.include_router(experiments.router,  prefix="/api/experiments",  tags=["experiments"])
app.include_router(validation.router,   prefix="/api/validation",   tags=["validation"])
app.include_router(reports.router,      prefix="/api/reports",      tags=["reports"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
