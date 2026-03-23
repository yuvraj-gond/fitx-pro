# =============================================================================
# backend/routers/profile.py
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..models.database import get_db, User, UserProfile
from ..models.schemas import ProfileCreate, ProfileOut
from ..services.auth import get_current_user
from ..services.ai_engine import calculate_nutrition_targets

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("", response_model=ProfileOut)
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.profile:
        raise HTTPException(404, "Profile not set up yet")
    return user.profile


@router.put("", response_model=ProfileOut)
def upsert_profile(
    data: ProfileCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    targets = calculate_nutrition_targets(
        data.weight_kg, data.height_cm, data.age,
        data.gender, data.activity_level, data.fitness_goal,
    )

    if user.profile:
        p = user.profile
    else:
        p = UserProfile(user_id=user.id)
        db.add(p)

    for field, val in data.model_dump().items():
        setattr(p, field, val)
    for field, val in targets.items():
        setattr(p, field, val)

    db.commit()
    db.refresh(p)
    return p
