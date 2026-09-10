"""Override API — Authorized soft-constraint override with audit log."""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.api.auth import get_current_user, require_admin
from app.models.override import Override

router = APIRouter()

# Hard constraints that cannot be overridden
HARD_CONSTRAINT_IDS = {"H1", "H2", "H3", "H4"}


class OverrideRequest(BaseModel):
    route_id: str
    constraint_id: str
    constraint_name: str
    reason: str
    previous_value: str
    new_decision: str
    notes: Optional[str] = ""


@router.post("")
async def create_override(
    req: OverrideRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Create an authorized override for a soft constraint."""
    if req.constraint_id in HARD_CONSTRAINT_IDS:
        raise HTTPException(
            status_code=403,
            detail=f"Constraint {req.constraint_id} ({req.constraint_name}) is a HARD CONSTRAINT and cannot be overridden. Hard safety constraints cannot be bypassed.",
        )

    override = Override(
        route_id=req.route_id,
        constraint_id=req.constraint_id,
        constraint_name=req.constraint_name,
        user_role=current_user["role"],
        user_id=current_user["username"],
        reason=req.reason,
        previous_value=req.previous_value,
        new_decision=req.new_decision,
        approved="approved",
        notes=req.notes or "",
    )
    db.add(override)
    db.commit()
    db.refresh(override)

    return {
        "success": True,
        "override_id": override.id,
        "message": f"Override approved for '{req.constraint_name}' on route {req.route_id}.",
        "approved_by": current_user["username"],
        "timestamp": override.created_at.isoformat(),
    }


@router.get("/log")
async def get_override_log(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Return the full override audit log."""
    overrides = db.query(Override).order_by(Override.created_at.desc()).all()
    return [
        {
            "id": o.id,
            "route_id": o.route_id,
            "constraint_id": o.constraint_id,
            "constraint_name": o.constraint_name,
            "user_id": o.user_id,
            "user_role": o.user_role,
            "reason": o.reason,
            "previous_value": o.previous_value,
            "new_decision": o.new_decision,
            "approved": o.approved,
            "created_at": o.created_at.isoformat(),
            "notes": o.notes,
        }
        for o in overrides
    ]
