"""Validation API — Stakeholder feedback form and satisfaction summary."""
import numpy as np
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional

from app.database import get_db
from app.api.auth import get_current_user
from app.models.validation_feedback import ValidationFeedback

router = APIRouter()


class FeedbackRequest(BaseModel):
    respondent_name: str = "Anonymous"
    respondent_role: str = "planner"
    q1_route_clarity: int = Field(ge=1, le=5)
    q2_operational_realism: int = Field(ge=1, le=5)
    q3_workload_useful: int = Field(ge=1, le=5)
    q4_comparison_useful: int = Field(ge=1, le=5)
    q5_fallback_clear: int = Field(ge=1, le=5)
    q6_would_use_daily: int = Field(ge=1, le=5)
    comments: Optional[str] = ""
    is_simulated: bool = True


@router.post("")
async def submit_feedback(
    req: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    scores = [req.q1_route_clarity, req.q2_operational_realism, req.q3_workload_useful,
              req.q4_comparison_useful, req.q5_fallback_clear, req.q6_would_use_daily]
    overall = round(sum(scores) / len(scores), 2)

    fb = ValidationFeedback(
        respondent_name=req.respondent_name,
        respondent_role=req.respondent_role,
        q1_route_clarity=req.q1_route_clarity,
        q2_operational_realism=req.q2_operational_realism,
        q3_workload_useful=req.q3_workload_useful,
        q4_comparison_useful=req.q4_comparison_useful,
        q5_fallback_clear=req.q5_fallback_clear,
        q6_would_use_daily=req.q6_would_use_daily,
        overall_score=overall,
        comments=req.comments or "",
        is_simulated=1 if req.is_simulated else 0,
    )
    db.add(fb)
    db.commit()

    return {
        "success": True,
        "overall_score": overall,
        "message": "Feedback recorded. Note: This is a prototype stakeholder simulation / pilot validation.",
        "is_simulated": req.is_simulated,
    }


@router.get("/summary")
async def get_validation_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    all_fb = db.query(ValidationFeedback).all()
    if not all_fb:
        return {"message": "No feedback submitted yet.", "n_responses": 0}

    scores = [f.overall_score for f in all_fb]
    q_scores = {
        "q1_route_clarity": np.mean([f.q1_route_clarity for f in all_fb]),
        "q2_operational_realism": np.mean([f.q2_operational_realism for f in all_fb]),
        "q3_workload_useful": np.mean([f.q3_workload_useful for f in all_fb]),
        "q4_comparison_useful": np.mean([f.q4_comparison_useful for f in all_fb]),
        "q5_fallback_clear": np.mean([f.q5_fallback_clear for f in all_fb]),
        "q6_would_use_daily": np.mean([f.q6_would_use_daily for f in all_fb]),
    }
    n_simulated = sum(1 for f in all_fb if f.is_simulated)
    return {
        "n_responses": len(all_fb),
        "n_simulated": n_simulated,
        "n_real": len(all_fb) - n_simulated,
        "avg_overall_score": round(float(np.mean(scores)), 2),
        "max_score": round(max(scores), 2),
        "min_score": round(min(scores), 2),
        "question_averages": {k: round(float(v), 2) for k, v in q_scores.items()},
        "validation_label": "Prototype stakeholder simulation / pilot validation",
        "responses": [
            {
                "respondent_name": f.respondent_name,
                "respondent_role": f.respondent_role,
                "overall_score": f.overall_score,
                "q1": f.q1_route_clarity, "q2": f.q2_operational_realism,
                "q3": f.q3_workload_useful, "q4": f.q4_comparison_useful,
                "q5": f.q5_fallback_clear, "q6": f.q6_would_use_daily,
                "comments": f.comments,
                "is_simulated": bool(f.is_simulated),
                "created_at": f.created_at.isoformat(),
            }
            for f in all_fb
        ],
    }
