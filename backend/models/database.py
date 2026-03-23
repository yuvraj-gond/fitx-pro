# =============================================================================
# backend/models/database.py
# SQLAlchemy ORM models + database initialisation
# =============================================================================

from sqlalchemy import (
    create_engine, Column, Integer, Float, String, Text,
    DateTime, Boolean, ForeignKey, Enum
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import enum
import os

# ── Database setup ──────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database/fitx.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite only
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── Enums ────────────────────────────────────────────────────────────────────
class FitnessGoal(str, enum.Enum):
    fat_loss     = "fat_loss"
    muscle_gain  = "muscle_gain"
    maintenance  = "maintenance"

class ActivityLevel(str, enum.Enum):
    sedentary   = "sedentary"
    light       = "light"
    moderate    = "moderate"
    very_active = "very_active"
    super_active = "super_active"

class Gender(str, enum.Enum):
    male   = "male"
    female = "female"
    other  = "other"

class SubscriptionTier(str, enum.Enum):
    free    = "free"
    premium = "premium"
    trainer = "trainer"

class MealType(str, enum.Enum):
    breakfast    = "breakfast"
    lunch        = "lunch"
    dinner       = "dinner"
    snack        = "snack"
    pre_workout  = "pre_workout"
    post_workout = "post_workout"


# =============================================================================
# ORM Models
# =============================================================================

class User(Base):
    """Core user account — authentication + subscription tier."""
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    username      = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    subscription  = Column(Enum(SubscriptionTier), default=SubscriptionTier.premium)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

    # Trainer relationship — a trainer can monitor many users
    trainer_id    = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    profile        = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete")
    nutrition_logs = relationship("NutritionLog", back_populates="user", cascade="all, delete")
    workout_logs   = relationship("WorkoutLog",   back_populates="user", cascade="all, delete")
    measurements   = relationship("BodyMeasurement", back_populates="user", cascade="all, delete")
    weight_logs    = relationship("WeightLog",    back_populates="user", cascade="all, delete")
    insights       = relationship("AIInsight",    back_populates="user", cascade="all, delete")
    clients        = relationship("User", foreign_keys=[trainer_id])


class UserProfile(Base):
    """Physical profile used for calorie / macro calculations."""
    __tablename__ = "user_profiles"

    id             = Column(Integer, primary_key=True)
    user_id        = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name           = Column(String(150))
    age            = Column(Integer)
    gender         = Column(Enum(Gender), default=Gender.male)
    height_cm      = Column(Float)
    weight_kg      = Column(Float)
    activity_level = Column(Enum(ActivityLevel), default=ActivityLevel.moderate)
    fitness_goal   = Column(Enum(FitnessGoal),  default=FitnessGoal.maintenance)

    # Calculated fields (updated on profile save)
    bmi              = Column(Float, nullable=True)
    bmr              = Column(Float, nullable=True)
    tdee             = Column(Float, nullable=True)
    target_calories  = Column(Integer, nullable=True)
    target_protein_g = Column(Float, nullable=True)
    target_carbs_g   = Column(Float, nullable=True)
    target_fat_g     = Column(Float, nullable=True)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")


class NutritionLog(Base):
    """Individual food entry logged by a user."""
    __tablename__ = "nutrition_logs"

    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date       = Column(String(10), nullable=False, index=True)   # YYYY-MM-DD
    food_name  = Column(String(200), nullable=False)
    quantity_g = Column(Float, nullable=False)
    meal_type  = Column(Enum(MealType), default=MealType.lunch)
    calories   = Column(Float, nullable=False)
    protein_g  = Column(Float, default=0)
    carbs_g    = Column(Float, default=0)
    fat_g      = Column(Float, default=0)
    logged_at  = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="nutrition_logs")


class WorkoutLog(Base):
    """A single exercise set logged by a user."""
    __tablename__ = "workout_logs"

    id           = Column(Integer, primary_key=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date         = Column(String(10), nullable=False, index=True)
    muscle_group = Column(String(50), nullable=False)
    exercise     = Column(String(150), nullable=False)
    sets         = Column(Integer, default=3)
    reps         = Column(Integer, default=10)
    weight_kg    = Column(Float, default=0)
    volume       = Column(Float, default=0)   # sets × reps × weight
    notes        = Column(Text, nullable=True)
    logged_at    = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="workout_logs")


class BodyMeasurement(Base):
    """Weekly body circumference measurements."""
    __tablename__ = "body_measurements"

    id           = Column(Integer, primary_key=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date         = Column(String(10), nullable=False)
    chest_cm     = Column(Float, nullable=True)
    biceps_cm    = Column(Float, nullable=True)
    waist_cm     = Column(Float, nullable=True)
    thigh_cm     = Column(Float, nullable=True)
    shoulders_cm = Column(Float, nullable=True)
    logged_at    = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="measurements")


class WeightLog(Base):
    """Daily body weight entry — used for trend prediction."""
    __tablename__ = "weight_logs"

    id        = Column(Integer, primary_key=True)
    user_id   = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date      = Column(String(10), nullable=False)
    weight_kg = Column(Float, nullable=False)
    logged_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="weight_logs")


class AIInsight(Base):
    """Persisted AI recommendations / alerts generated for a user."""
    __tablename__ = "ai_insights"

    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date       = Column(String(10), nullable=False)
    category   = Column(String(50))           # nutrition / workout / recovery / progress
    priority   = Column(Integer, default=2)   # 1=high 2=medium 3=positive
    title      = Column(String(200))
    message    = Column(Text)
    action     = Column(Text)
    is_read    = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="insights")


# =============================================================================
# Food reference table (seeded once)
# =============================================================================
class Food(Base):
    """Read-only food reference database."""
    __tablename__ = "foods"

    id                 = Column(Integer, primary_key=True)
    name               = Column(String(200), unique=True, nullable=False, index=True)
    calories_per_100g  = Column(Float)
    protein_per_100g   = Column(Float)
    carbs_per_100g     = Column(Float)
    fat_per_100g       = Column(Float)
    category           = Column(String(50))


# =============================================================================
# DB Init helpers
# =============================================================================
def create_tables():
    import os
    os.makedirs("database", exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency — yields a DB session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
