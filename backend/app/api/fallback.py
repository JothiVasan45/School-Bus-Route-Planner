"""
Fallback API — Offline mode, manual fallback, and store-and-forward sync.
Handles GPS failure, network failure, and manual stop updates.
"""
import json
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.api.auth import get_current_user
from app.models.fallback_event import FallbackEvent
from app.models.sync_queue import SyncQueue
from app.models.route import Route, RouteStop

router = APIRouter()

# In-memory system status (simulated)
_system_status = {
    "gps": "ONLINE",
    "network": "ONLINE",
    "attendance_feed": "ONLINE",
    "traffic_feed": "ONLINE",
}


class ToggleRequest(BaseModel):
    event_type: str   # gps_failure | network_failure | attendance_feed_failure | traffic_feed_failure
    active: bool
    route_id: Optional[str] = None
    driver_id: Optional[str] = None


class ManualUpdateRequest(BaseModel):
    route_id: str
    stop_id: str
    update_type: str     # arrived | departed | student_count | delay
    driver_id: str
    actual_time: Optional[str] = None
    student_count: Optional[int] = None
    delay_reason: Optional[str] = None


_EVENT_TO_STATUS_KEY = {
    "gps_failure": "gps",
    "network_failure": "network",
    "attendance_feed_failure": "attendance_feed",
    "traffic_feed_failure": "traffic_feed",
}


@router.get("/status")
async def get_system_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return current system status (GPS, network, feeds)."""
    active_events = db.query(FallbackEvent).filter(FallbackEvent.resolved == False).all()
    status = {
        "gps": "ONLINE",
        "network": "ONLINE",
        "attendance_feed": "ONLINE",
        "traffic_feed": "ONLINE",
    }
    for ev in active_events:
        key = _EVENT_TO_STATUS_KEY.get(ev.event_type)
        if key:
            status[key] = "OFFLINE"

    pending_sync = db.query(SyncQueue).filter(SyncQueue.synced == 0).count()
    return {
        "status": status,
        "active_failures": len(active_events),
        "pending_sync_count": pending_sync,
        "offline_mode": status["network"] == "OFFLINE",
    }


@router.post("/toggle")
async def toggle_failure(
    req: ToggleRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Toggle a simulated system failure on/off."""
    valid_types = list(_EVENT_TO_STATUS_KEY.keys())
    if req.event_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"event_type must be one of {valid_types}")

    if req.active:
        # Create failure event
        ev = FallbackEvent(
            event_type=req.event_type,
            triggered_by=current_user["username"],
            route_id=req.route_id,
            driver_id=req.driver_id,
            fallback_mode="offline" if req.event_type == "network_failure" else "cached",
            description=f"Simulated {req.event_type} triggered by {current_user['username']}",
            resolved=False,
        )
        db.add(ev)
        db.commit()
        return {
            "success": True,
            "message": f"{req.event_type} activated. System entering fallback mode.",
            "fallback_mode": ev.fallback_mode,
        }
    else:
        # Resolve existing events of this type
        events = db.query(FallbackEvent).filter(
            FallbackEvent.event_type == req.event_type,
            FallbackEvent.resolved == False,
        ).all()
        for ev in events:
            ev.resolved = True
            ev.resolved_at = datetime.utcnow()
        db.commit()
        return {
            "success": True,
            "message": f"{req.event_type} resolved. System back online.",
        }


@router.post("/manual-update")
async def manual_stop_update(
    req: ManualUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Store a manual stop update (used when GPS is unavailable)."""
    update_data = {
        "actual_time": req.actual_time,
        "student_count": req.student_count,
        "delay_reason": req.delay_reason,
    }

    # Check if network is down — queue the update
    network_down = db.query(FallbackEvent).filter(
        FallbackEvent.event_type == "network_failure",
        FallbackEvent.resolved == False,
    ).first() is not None

    queue_item = SyncQueue(
        route_id=req.route_id,
        stop_id=req.stop_id,
        update_type=req.update_type,
        update_data=json.dumps(update_data),
        synced=0,
        driver_id=req.driver_id,
    )
    db.add(queue_item)

    # If network is available, also immediately update the route stop
    if not network_down:
        rs = db.query(RouteStop).filter(
            RouteStop.route_id == req.route_id,
            RouteStop.stop_id == req.stop_id,
        ).first()
        if rs:
            if req.update_type == "arrived" and req.actual_time:
                rs.actual_arrival = req.actual_time
            elif req.update_type == "departed" and req.actual_time:
                rs.actual_departure = req.actual_time
                rs.is_completed = True
            if req.student_count is not None:
                rs.students_boarded = req.student_count
            if req.delay_reason:
                rs.delay_reason = req.delay_reason
        queue_item.synced = 1
        queue_item.synced_at = datetime.utcnow()

    db.commit()

    return {
        "success": True,
        "queued": network_down,
        "message": "Update queued for sync." if network_down else "Update applied immediately.",
        "sync_queue_id": queue_item.id,
    }


@router.post("/sync")
async def sync_queue(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Sync all queued updates when network comes back online."""
    # Check if network is still down
    network_down = db.query(FallbackEvent).filter(
        FallbackEvent.event_type == "network_failure",
        FallbackEvent.resolved == False,
    ).first() is not None

    if network_down:
        raise HTTPException(status_code=503, detail="Network still offline. Cannot sync.")

    pending = db.query(SyncQueue).filter(SyncQueue.synced == 0).all()
    synced_count = 0

    for item in pending:
        # Apply each queued update
        try:
            data = json.loads(item.update_data)
            rs = db.query(RouteStop).filter(
                RouteStop.route_id == item.route_id,
                RouteStop.stop_id == item.stop_id,
            ).first()
            if rs:
                if item.update_type == "arrived" and data.get("actual_time"):
                    rs.actual_arrival = data["actual_time"]
                elif item.update_type == "departed" and data.get("actual_time"):
                    rs.actual_departure = data["actual_time"]
                    rs.is_completed = True
                if data.get("student_count") is not None:
                    rs.students_boarded = data["student_count"]
                if data.get("delay_reason"):
                    rs.delay_reason = data["delay_reason"]
            item.synced = 1
            item.synced_at = datetime.utcnow()
            synced_count += 1
        except Exception as e:
            continue

    db.commit()

    return {
        "success": True,
        "synced_count": synced_count,
        "message": f"Synchronized {synced_count} queued update(s) successfully.",
    }


@router.get("/queue")
async def get_sync_queue(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return pending sync queue items."""
    pending = db.query(SyncQueue).filter(SyncQueue.synced == 0).all()
    return {
        "pending_count": len(pending),
        "items": [
            {
                "id": item.id,
                "route_id": item.route_id,
                "stop_id": item.stop_id,
                "update_type": item.update_type,
                "driver_id": item.driver_id,
                "queued_at": item.queued_at.isoformat(),
            }
            for item in pending
        ],
    }


@router.get("/events")
async def get_fallback_events(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return all fallback events (history)."""
    events = db.query(FallbackEvent).order_by(FallbackEvent.created_at.desc()).limit(50).all()
    return [
        {
            "id": ev.id,
            "event_type": ev.event_type,
            "triggered_by": ev.triggered_by,
            "fallback_mode": ev.fallback_mode,
            "description": ev.description,
            "resolved": ev.resolved,
            "resolved_at": ev.resolved_at.isoformat() if ev.resolved_at else None,
            "created_at": ev.created_at.isoformat(),
        }
        for ev in events
    ]
