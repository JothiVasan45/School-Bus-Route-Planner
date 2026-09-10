"""Routes API — Proxy to optimization.py list/get."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.auth import get_current_user
from app.api.optimization import list_routes, get_route

router = APIRouter()

router.add_api_route("", list_routes, methods=["GET"])
router.add_api_route("/{route_id}", get_route, methods=["GET"])
