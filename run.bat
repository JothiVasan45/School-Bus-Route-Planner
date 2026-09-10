@echo off
title School-Bus Route Planner
echo ======================================================================
echo    Multi-Objective School-Bus Route Planner
echo    Variable Student Attendance ^& Service Reliability
echo ======================================================================
echo.

cd /d "%~dp0"

echo [1/4] Checking Python environment...
python --version
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    pause
    exit /b 1
)

echo [2/4] Generating initial synthetic dataset if not present...
if not exist "data\synthetic\stops.csv" (
    python scripts\generate_data.py
)

echo [3/4] Starting FastAPI Backend on http://localhost:8000 ...
start "School-Bus Backend (FastAPI)" cmd /k "cd backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

echo [4/4] Starting Vite Frontend on http://localhost:5173 ...
start "School-Bus Frontend (Vite)" cmd /k "cd frontend && npm run dev"

echo.
echo ======================================================================
echo System started successfully!
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo   Demo Login: admin / admin123
echo ======================================================================
echo.
pause
