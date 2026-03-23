# =============================================================================
# backend/routers/insights.py
# AI Insights, body measurements, weight logs
# =============================================================================

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import date, timedelta
from ..models.database import get_db, User, AIInsight, BodyMeasurement, WeightLog
from ..models.schemas import (
    InsightOut, MeasurementCreate, MeasurementOut,
    WeightLogCreate, WeightLogOut,
)
from ..services.auth import get_current_user
from ..services.ai_engine import (
    generate_daily_alerts, generate_weekly_summary,
    predict_weight_trend, get_nutrition_budget,
)

router = APIRouter(prefix="/insights", tags=["AI Insights"])


# ── Helper: rebuild & persist today's alerts ─────────────────────────────────
def _refresh_alerts(user: User, db: Session):
    """Delete today's unseen alerts and regenerate."""
    today = date.today().isoformat()
    db.query(AIInsight).filter(
        AIInsight.user_id == user.id,
        AIInsight.date == today,
        AIInsight.is_read == False,
    ).delete()

    # Gather data
    profile_data = None
    if user.profile:
        p = user.profile
        profile_data = {
            "target_calories": p.target_calories,
            "target_protein_g": p.target_protein_g,
            "fitness_goal": p.fitness_goal,
        }

    from ..models.database import NutritionLog, WorkoutLog
    from sqlalchemy import func

    nut = db.query(
        func.sum(NutritionLog.calories).label("total_calories"),
        func.sum(NutritionLog.protein_g).label("total_protein"),
    ).filter(NutritionLog.user_id == user.id, NutritionLog.date == today).one()

    today_nutrition = {
        "total_calories": nut.total_calories or 0,
        "total_protein":  nut.total_protein  or 0,
    } if nut else None

    workouts = db.query(WorkoutLog).filter(WorkoutLog.user_id == user.id).order_by(
        WorkoutLog.date.desc()
    ).limit(60).all()
    recent_workouts = [
        {"date": w.date, "muscle_group": w.muscle_group,
         "exercise": w.exercise, "volume": w.volume}
        for w in workouts
    ]

    measurements = db.query(BodyMeasurement).filter(
        BodyMeasurement.user_id == user.id
    ).order_by(BodyMeasurement.date).all()
    recent_meas = [{"waist_cm": m.waist_cm} for m in measurements]

    alerts = generate_daily_alerts(profile_data, today_nutrition, recent_workouts, recent_meas)

    for a in alerts:
        db.add(AIInsight(
            user_id=user.id, date=today,
            category=a["category"], priority=a["priority"],
            title=a["title"], message=a["message"], action=a["action"],
        ))
    db.commit()


# ── Endpoints ──────────────────────────────────────────────────────────────
@router.get("", response_model=List[InsightOut])
def get_insights(
    refresh: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return AI insights. Pass ?refresh=true to regenerate today's alerts."""
    if refresh:
        _refresh_alerts(user, db)
    return db.query(AIInsight).filter(
        AIInsight.user_id == user.id
    ).order_by(AIInsight.created_at.desc()).limit(30).all()


@router.patch("/{insight_id}/read", response_model=InsightOut)
def mark_read(
    insight_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ins = db.query(AIInsight).filter(
        AIInsight.id == insight_id, AIInsight.user_id == user.id
    ).first()
    if ins:
        ins.is_read = True
        db.commit()
        db.refresh(ins)
    return ins


@router.get("/weekly-summary")
def weekly_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from ..models.database import NutritionLog, WorkoutLog
    from sqlalchemy import func

    cutoff = (date.today() - timedelta(days=6)).isoformat()
    nut_rows = db.query(
        NutritionLog.date,
        func.sum(NutritionLog.calories).label("total_calories"),
        func.sum(NutritionLog.protein_g).label("total_protein"),
    ).filter(
        NutritionLog.user_id == user.id, NutritionLog.date >= cutoff
    ).group_by(NutritionLog.date).all()

    wk_rows = db.query(WorkoutLog).filter(
        WorkoutLog.user_id == user.id, WorkoutLog.date >= cutoff
    ).all()

    profile_data = None
    if user.profile:
        p = user.profile
        profile_data = {
            "target_calories": p.target_calories,
            "target_protein_g": p.target_protein_g,
        }

    nutrition_week = [{"total_calories": r.total_calories, "total_protein": r.total_protein}
                      for r in nut_rows]
    workouts_week  = [{"date": w.date, "muscle_group": w.muscle_group, "volume": w.volume}
                      for w in wk_rows]

    return generate_weekly_summary(nutrition_week, workouts_week, profile_data)


@router.get("/weight-prediction")
def weight_prediction(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logs = db.query(WeightLog).filter(
        WeightLog.user_id == user.id
    ).order_by(WeightLog.date).all()
    history = [{"date": w.date, "weight_kg": w.weight_kg} for w in logs]
    return predict_weight_trend(history, days_ahead=30)


@router.get("/budget")
def nutrition_budget(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from ..models.database import NutritionLog
    from sqlalchemy import func

    today = date.today().isoformat()
    nut = db.query(
        func.sum(NutritionLog.calories).label("cal"),
        func.sum(NutritionLog.protein_g).label("prot"),
        func.sum(NutritionLog.carbs_g).label("carbs"),
        func.sum(NutritionLog.fat_g).label("fat"),
    ).filter(NutritionLog.user_id == user.id, NutritionLog.date == today).one()

    today_totals = {
        "total_calories": nut.cal   or 0,
        "total_protein":  nut.prot  or 0,
        "total_carbs":    nut.carbs or 0,
        "total_fat":      nut.fat   or 0,
    }
    if not user.profile:
        return today_totals

    p = user.profile
    profile_data = {
        "target_calories":  p.target_calories,
        "target_protein_g": p.target_protein_g,
        "target_carbs_g":   p.target_carbs_g,
        "target_fat_g":     p.target_fat_g,
    }
    return get_nutrition_budget(profile_data, today_totals)


# ── Body Measurements ──────────────────────────────────────────────────────
meas_router = APIRouter(prefix="/measurements", tags=["Measurements"])


@meas_router.post("", response_model=MeasurementOut, status_code=201)
def add_measurement(
    data: MeasurementCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    m = BodyMeasurement(user_id=user.id, **data.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@meas_router.get("", response_model=List[MeasurementOut])
def get_measurements(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(BodyMeasurement).filter(
        BodyMeasurement.user_id == user.id
    ).order_by(BodyMeasurement.date).all()


# ── Weight Logs ────────────────────────────────────────────────────────────
weight_router = APIRouter(prefix="/weight", tags=["Weight"])


@weight_router.post("", response_model=WeightLogOut, status_code=201)
def log_weight(
    data: WeightLogCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    w = WeightLog(user_id=user.id, **data.model_dump())
    db.add(w)
    db.commit()
    db.refresh(w)
    return w


@weight_router.get("", response_model=List[WeightLogOut])
def get_weight(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(WeightLog).filter(
        WeightLog.user_id == user.id
    ).order_by(WeightLog.date).all()
