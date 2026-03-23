# =============================================================================
# backend/routers/trainer.py
# Trainer dashboard — monitor clients (trainer-tier only)
# =============================================================================

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..models.database import get_db, User
from ..models.schemas import UserOut
from ..services.auth import require_trainer

router = APIRouter(prefix="/trainer", tags=["Trainer"])


@router.get("/clients", response_model=List[UserOut])
def list_clients(
    trainer: User = Depends(require_trainer),
    db: Session = Depends(get_db),
):
    """Return all users assigned to this trainer."""
    return db.query(User).filter(User.trainer_id == trainer.id).all()


@router.get("/clients/{client_id}/summary")
def client_summary(
    client_id: int,
    trainer: User = Depends(require_trainer),
    db: Session = Depends(get_db),
):
    from ..models.database import NutritionLog, WorkoutLog
    from sqlalchemy import func
    from datetime import date, timedelta

    client = db.query(User).filter(
        User.id == client_id, User.trainer_id == trainer.id
    ).first()
    if not client:
        from fastapi import HTTPException
        raise HTTPException(404, "Client not found or not assigned to you")

    cutoff = (date.today() - timedelta(days=7)).isoformat()

    cal_row = db.query(func.sum(NutritionLog.calories)).filter(
        NutritionLog.user_id == client_id,
        NutritionLog.date >= cutoff,
    ).scalar() or 0

    workout_count = db.query(WorkoutLog).filter(
        WorkoutLog.user_id == client_id,
        WorkoutLog.date >= cutoff,
    ).count()

    profile = client.profile
    return {
        "client": {"id": client.id, "username": client.username, "email": client.email},
        "profile": {
            "goal": profile.fitness_goal if profile else None,
            "weight_kg": profile.weight_kg if profile else None,
            "target_calories": profile.target_calories if profile else None,
        },
        "week_summary": {
            "total_calories": round(cal_row, 1),
            "workout_sessions": workout_count,
        },
    }
