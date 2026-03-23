# =============================================================================
# backend/routers/nutrition.py
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import date
from ..models.database import get_db, User, NutritionLog, Food
from ..models.schemas import NutritionLogCreate, NutritionLogOut, DailyNutritionSummary, FoodOut
from ..services.auth import get_current_user

router = APIRouter(prefix="/nutrition", tags=["Nutrition"])


@router.get("/foods", response_model=List[FoodOut])
def list_foods(
    search: str = Query("", max_length=100),
    db: Session = Depends(get_db),
):
    q = db.query(Food)
    if search:
        q = q.filter(Food.name.ilike(f"%{search}%"))
    return q.order_by(Food.name).all()


@router.post("/log", response_model=NutritionLogOut, status_code=201)
def log_food(
    data: NutritionLogCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = NutritionLog(user_id=user.id, **data.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/log", response_model=List[NutritionLogOut])
def get_logs(
    date_str: str = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(NutritionLog).filter(NutritionLog.user_id == user.id)
    if date_str:
        q = q.filter(NutritionLog.date == date_str)
    return q.order_by(NutritionLog.logged_at.desc()).all()


@router.delete("/log/{entry_id}", status_code=204)
def delete_log(
    entry_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = db.query(NutritionLog).filter(
        NutritionLog.id == entry_id, NutritionLog.user_id == user.id
    ).first()
    if not entry:
        raise HTTPException(404, "Entry not found")
    db.delete(entry)
    db.commit()


@router.get("/summary", response_model=DailyNutritionSummary)
def daily_summary(
    date_str: str = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target_date = date_str or date.today().isoformat()
    rows = db.query(NutritionLog).filter(
        NutritionLog.user_id == user.id,
        NutritionLog.date == target_date,
    ).all()

    total_cal  = sum(r.calories  for r in rows)
    total_prot = sum(r.protein_g for r in rows)
    total_carbs = sum(r.carbs_g  for r in rows)
    total_fat  = sum(r.fat_g     for r in rows)

    profile = user.profile
    tgt_cal  = profile.target_calories  if profile else 2000
    tgt_prot = profile.target_protein_g if profile else 150

    return DailyNutritionSummary(
        date=target_date,
        total_calories=total_cal,
        total_protein=total_prot,
        total_carbs=total_carbs,
        total_fat=total_fat,
        target_calories=tgt_cal,
        target_protein=tgt_prot,
        calorie_pct=min(100, total_cal / tgt_cal * 100) if tgt_cal else 0,
        protein_pct=min(100, total_prot / tgt_prot * 100) if tgt_prot else 0,
    )


@router.get("/weekly", response_model=List[dict])
def weekly_nutrition(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return last-7-days daily aggregates for chart rendering."""
    from datetime import timedelta
    rows = db.query(
        NutritionLog.date,
        func.sum(NutritionLog.calories).label("calories"),
        func.sum(NutritionLog.protein_g).label("protein"),
        func.sum(NutritionLog.carbs_g).label("carbs"),
        func.sum(NutritionLog.fat_g).label("fat"),
    ).filter(
        NutritionLog.user_id == user.id,
        NutritionLog.date >= (date.today() - timedelta(days=6)).isoformat(),
    ).group_by(NutritionLog.date).order_by(NutritionLog.date).all()

    return [{"date": r.date, "calories": r.calories or 0,
             "protein": r.protein or 0, "carbs": r.carbs or 0, "fat": r.fat or 0}
            for r in rows]
