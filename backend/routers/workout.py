# =============================================================================
# backend/routers/workout.py
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import date, timedelta
from ..models.database import get_db, User, WorkoutLog
from ..models.schemas import WorkoutLogCreate, WorkoutLogOut
from ..services.auth import get_current_user

router = APIRouter(prefix="/workout", tags=["Workout"])

EXERCISES = {
    "Chest":     ["Bench Press","Incline Bench Press","Decline Bench Press","Dumbbell Fly","Push-Ups","Cable Fly","Chest Dip"],
    "Back":      ["Deadlift","Pull Ups","Barbell Row","Dumbbell Row","Lat Pulldown","Seated Cable Row","Face Pull"],
    "Biceps":    ["Barbell Curl","Dumbbell Curl","Hammer Curl","Concentration Curl","Preacher Curl","Cable Curl"],
    "Triceps":   ["Tricep Pushdown","Close Grip Bench","Skull Crusher","Overhead Tricep Extension","Tricep Dip"],
    "Legs":      ["Squat","Romanian Deadlift","Leg Press","Hack Squat","Leg Extension","Leg Curl","Calf Raise","Lunges"],
    "Shoulders": ["Overhead Press","Lateral Raise","Front Raise","Rear Delt Fly","Arnold Press","Shrugs"],
    "Core":      ["Plank","Crunches","Russian Twist","Leg Raise","Ab Wheel","Hanging Leg Raise"],
    "Cardio":    ["Running","Cycling","Jump Rope","HIIT","Swimming","Rowing Machine"],
}


@router.get("/exercises")
def get_exercises():
    return EXERCISES


@router.post("/log", response_model=WorkoutLogOut, status_code=201)
def log_workout(
    data: WorkoutLogCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    volume = data.sets * data.reps * data.weight_kg
    entry = WorkoutLog(user_id=user.id, volume=volume, **data.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/log", response_model=List[WorkoutLogOut])
def get_logs(
    date_str: str = Query(default=None),
    limit: int = Query(default=50, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(WorkoutLog).filter(WorkoutLog.user_id == user.id)
    if date_str:
        q = q.filter(WorkoutLog.date == date_str)
    return q.order_by(WorkoutLog.logged_at.desc()).limit(limit).all()


@router.delete("/log/{entry_id}", status_code=204)
def delete_workout(
    entry_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = db.query(WorkoutLog).filter(
        WorkoutLog.id == entry_id, WorkoutLog.user_id == user.id
    ).first()
    if not entry:
        raise HTTPException(404, "Entry not found")
    db.delete(entry)
    db.commit()


@router.get("/stats")
def workout_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Muscle-group frequency + weekly volume for analytics charts."""
    cutoff_30 = (date.today() - timedelta(days=30)).isoformat()
    rows = db.query(WorkoutLog).filter(
        WorkoutLog.user_id == user.id,
        WorkoutLog.date >= cutoff_30,
    ).all()

    mg_freq: dict = {}
    weekly_vol: dict = {}
    for r in rows:
        mg_freq[r.muscle_group] = mg_freq.get(r.muscle_group, 0) + 1
        weekly_vol[r.date] = weekly_vol.get(r.date, 0) + (r.volume or 0)

    return {"muscle_frequency": mg_freq, "daily_volume": weekly_vol}


@router.get("/streak")
def training_streak(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.query(WorkoutLog.date).filter(
        WorkoutLog.user_id == user.id
    ).distinct().order_by(WorkoutLog.date.desc()).all()

    dates = sorted({r.date for r in rows}, reverse=True)
    streak = 0
    check = date.today().isoformat()
    for d in dates:
        if d == check:
            streak += 1
            check = (date.fromisoformat(check) - timedelta(days=1)).isoformat()
        elif d < check:
            break
    return {"streak": streak}


@router.get("/exercise-history/{exercise_name}")
def get_exercise_history(
    exercise_name: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch PR (max weight) and last logged session for a specific exercise."""
    # Find PR based on absolute max weight
    pr_record = db.query(WorkoutLog).filter(
        WorkoutLog.user_id == user.id,
        WorkoutLog.exercise == exercise_name
    ).order_by(WorkoutLog.weight_kg.desc(), WorkoutLog.volume.desc()).first()

    # Find the most recent session
    last_record = db.query(WorkoutLog).filter(
        WorkoutLog.user_id == user.id,
        WorkoutLog.exercise == exercise_name
    ).order_by(WorkoutLog.date.desc(), WorkoutLog.id.desc()).first()

    pr_data = None
    if pr_record and pr_record.weight_kg > 0:
        pr_data = {
            "weight": pr_record.weight_kg, 
            "reps": pr_record.reps, 
            "volume": pr_record.volume
        }
    
    last_data = None
    if last_record:
        last_data = {
            "date": last_record.date, 
            "weight": last_record.weight_kg, 
            "reps": last_record.reps, 
            "sets": last_record.sets,
            "volume": last_record.volume
        }

    return {"pr": pr_data, "last_workout": last_data}

