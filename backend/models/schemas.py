# =============================================================================
# backend/models/schemas.py
# Pydantic v2 schemas for request validation and response serialisation
# =============================================================================

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from .database import FitnessGoal, ActivityLevel, Gender, SubscriptionTier, MealType


# ── Auth ─────────────────────────────────────────────────────────────────────
class UserRegister(BaseModel):
    email:    EmailStr
    username: str
    password: str

    @field_validator("password")
    @classmethod
    def strong_password(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserLogin(BaseModel):
    email:    EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user_id:      int
    username:     str
    subscription: str


class UserOut(BaseModel):
    id:           int
    email:        str
    username:     str
    subscription: str
    created_at:   datetime

    class Config:
        from_attributes = True


# ── Profile ───────────────────────────────────────────────────────────────────
class ProfileCreate(BaseModel):
    name:           str
    age:            int
    gender:         Gender
    height_cm:      float
    weight_kg:      float
    activity_level: ActivityLevel
    fitness_goal:   FitnessGoal


class ProfileOut(ProfileCreate):
    bmi:              Optional[float]
    bmr:              Optional[float]
    tdee:             Optional[float]
    target_calories:  Optional[int]
    target_protein_g: Optional[float]
    target_carbs_g:   Optional[float]
    target_fat_g:     Optional[float]
    updated_at:       Optional[datetime]

    class Config:
        from_attributes = True


# ── Nutrition ─────────────────────────────────────────────────────────────────
class NutritionLogCreate(BaseModel):
    date:       str          # YYYY-MM-DD
    food_name:  str
    quantity_g: float
    meal_type:  MealType
    calories:   float
    protein_g:  float = 0
    carbs_g:    float = 0
    fat_g:      float = 0


class NutritionLogOut(NutritionLogCreate):
    id:        int
    logged_at: datetime

    class Config:
        from_attributes = True


class DailyNutritionSummary(BaseModel):
    date:           str
    total_calories: float
    total_protein:  float
    total_carbs:    float
    total_fat:      float
    target_calories: Optional[int]
    target_protein:  Optional[float]
    calorie_pct:    float
    protein_pct:    float


# ── Workout ───────────────────────────────────────────────────────────────────
class WorkoutLogCreate(BaseModel):
    date:         str
    muscle_group: str
    exercise:     str
    sets:         int
    reps:         int
    weight_kg:    float = 0
    notes:        Optional[str] = None


class WorkoutLogOut(WorkoutLogCreate):
    id:        int
    volume:    float
    logged_at: datetime

    class Config:
        from_attributes = True


# ── Body Measurements ─────────────────────────────────────────────────────────
class MeasurementCreate(BaseModel):
    date:         str
    chest_cm:     Optional[float] = None
    biceps_cm:    Optional[float] = None
    waist_cm:     Optional[float] = None
    thigh_cm:     Optional[float] = None
    shoulders_cm: Optional[float] = None


class MeasurementOut(MeasurementCreate):
    id:        int
    logged_at: datetime

    class Config:
        from_attributes = True


# ── Weight ────────────────────────────────────────────────────────────────────
class WeightLogCreate(BaseModel):
    date:      str
    weight_kg: float


class WeightLogOut(WeightLogCreate):
    id:        int
    logged_at: datetime

    class Config:
        from_attributes = True


# ── Food DB ───────────────────────────────────────────────────────────────────
class FoodOut(BaseModel):
    id:                int
    name:              str
    calories_per_100g: float
    protein_per_100g:  float
    carbs_per_100g:    float
    fat_per_100g:      float
    category:          str

    class Config:
        from_attributes = True


# ── AI Insights ───────────────────────────────────────────────────────────────
class InsightOut(BaseModel):
    id:         int
    date:       str
    category:   str
    priority:   int
    title:      str
    message:    str
    action:     str
    is_read:    bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Dashboard ─────────────────────────────────────────────────────────────────
class DashboardData(BaseModel):
    profile:           Optional[ProfileOut]
    today_nutrition:   Optional[DailyNutritionSummary]
    recent_workouts:   List[WorkoutLogOut]
    weight_trend:      List[WeightLogOut]
    unread_insights:   int
    streak:            int
    weekly_cal_data:   List[dict]
    weekly_prot_data:  List[dict]
    muscle_freq:       dict
