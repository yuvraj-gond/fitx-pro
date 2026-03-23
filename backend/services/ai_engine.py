# =============================================================================
# backend/services/ai_engine.py
# Rule-based AI engine + simple linear regression weight predictor
# =============================================================================

from __future__ import annotations
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
import numpy as np


# =============================================================================
# 1. NUTRITION CALCULATIONS (Mifflin-St Jeor + goal adjustments)
# =============================================================================

ACTIVITY_MULTIPLIERS = {
    "sedentary":    1.2,
    "light":        1.375,
    "moderate":     1.55,
    "very_active":  1.725,
    "super_active": 1.9,
}

GOAL_CAL_DELTA = {
    "fat_loss":    -500,
    "muscle_gain": +300,
    "maintenance":  0,
}

GOAL_PROTEIN_FACTOR = {
    "fat_loss":    2.2,
    "muscle_gain": 2.0,
    "maintenance": 1.6,
}


def calculate_nutrition_targets(
    weight_kg: float, height_cm: float, age: int,
    gender: str, activity_level: str, fitness_goal: str
) -> Dict[str, float]:
    """Return BMI, BMR, TDEE, and macro targets."""
    # BMI
    h = height_cm / 100
    bmi = round(weight_kg / h**2, 1)

    # Mifflin-St Jeor BMR
    if gender == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    tdee = bmr * ACTIVITY_MULTIPLIERS.get(activity_level, 1.55)
    target_cal = round(tdee + GOAL_CAL_DELTA.get(fitness_goal, 0))

    protein_g = round(weight_kg * GOAL_PROTEIN_FACTOR.get(fitness_goal, 1.8), 1)
    fat_g     = round(target_cal * 0.25 / 9, 1)          # 25% calories from fat
    carbs_g   = round((target_cal - protein_g*4 - fat_g*9) / 4, 1)  # remainder

    return {
        "bmi":              bmi,
        "bmr":              round(bmr, 1),
        "tdee":             round(tdee, 1),
        "target_calories":  int(target_cal),
        "target_protein_g": protein_g,
        "target_carbs_g":   max(carbs_g, 0),
        "target_fat_g":     fat_g,
    }


# =============================================================================
# 2. SMART ALERT GENERATOR
# =============================================================================

def generate_daily_alerts(
    profile_data: Optional[dict],
    today_nutrition: Optional[dict],
    recent_workouts: List[dict],
    recent_measurements: List[dict],
) -> List[Dict[str, Any]]:
    """
    Analyse today's data and return a list of actionable smart alerts.
    Each alert: {category, priority, title, message, action}
    """
    alerts = []
    today = date.today().isoformat()

    if not profile_data:
        return [{
            "category": "setup", "priority": 1,
            "title": "Profile Incomplete",
            "message": "Set up your profile to unlock personalised recommendations.",
            "action": "Go to Settings → Profile and fill in your details.",
        }]

    target_cal  = profile_data.get("target_calories", 2000)
    target_prot = profile_data.get("target_protein_g", 150)
    goal        = profile_data.get("fitness_goal", "maintenance")

    # ── Nutrition alerts ─────────────────────────────────────────────────────
    if today_nutrition:
        cal  = today_nutrition.get("total_calories", 0)
        prot = today_nutrition.get("total_protein", 0)

        if cal > target_cal * 1.15:
            alerts.append({
                "category": "nutrition", "priority": 1,
                "title": "⚠️ Calorie Limit Exceeded",
                "message": f"You've consumed {cal:.0f} kcal today — {cal - target_cal:.0f} kcal over your target of {target_cal} kcal.",
                "action": "Skip your next snack and opt for a lighter dinner.",
            })
        elif cal < target_cal * 0.6 and cal > 0:
            alerts.append({
                "category": "nutrition", "priority": 1,
                "title": "🍽️ Severe Under-Eating",
                "message": f"You've only had {cal:.0f} kcal — just {cal/target_cal*100:.0f}% of your {target_cal} kcal target.",
                "action": "Add a protein-rich meal or shake now. Chronic under-eating slows metabolism.",
            })

        if prot < target_prot * 0.7 and prot > 0:
            alerts.append({
                "category": "nutrition", "priority": 1,
                "title": "🥩 Protein Intake Too Low",
                "message": f"You've only consumed {prot:.1f}g protein — {target_prot - prot:.1f}g short of your {target_prot}g target.",
                "action": "Add chicken breast, Greek yogurt, eggs, or a whey protein shake.",
            })
        elif prot >= target_prot * 0.9:
            alerts.append({
                "category": "nutrition", "priority": 3,
                "title": "✅ Protein Goal On Track",
                "message": f"Great job! You've hit {prot:.1f}g / {target_prot}g protein today.",
                "action": "Keep it up — consistency is the key to muscle growth.",
            })

    # ── Workout alerts ────────────────────────────────────────────────────────
    all_muscle_groups = ["Chest", "Back", "Legs", "Shoulders", "Biceps", "Triceps"]
    cutoff_14 = (date.today() - timedelta(days=14)).isoformat()
    recent_mg = [w["muscle_group"] for w in recent_workouts if w.get("date", "") >= cutoff_14]

    for mg in all_muscle_groups:
        if mg not in recent_mg:
            alerts.append({
                "category": "workout", "priority": 2,
                "title": f"🏋️ {mg} Not Trained in 14 Days",
                "message": f"Your {mg.lower()} hasn't been trained recently.",
                "action": f"Schedule a {mg.lower()} session this week for balanced development.",
            })

    # Volume stagnation check
    exercise_volumes: Dict[str, List[float]] = {}
    for w in recent_workouts:
        ex = w.get("exercise", "")
        vol = w.get("volume", 0)
        exercise_volumes.setdefault(ex, []).append(vol)

    for ex, vols in exercise_volumes.items():
        if len(vols) >= 3 and np.std(vols) < 5 and np.mean(vols) > 0:
            alerts.append({
                "category": "workout", "priority": 2,
                "title": f"📈 Stagnation Detected: {ex}",
                "message": f"Your {ex} volume hasn't changed in {len(vols)} sessions.",
                "action": "Try adding 2.5–5 kg or increase reps by 2 to break the plateau.",
            })

    # Progressive overload check
    exercise_maxes: Dict[str, List[float]] = {}
    for w in recent_workouts:
        ex = w.get("exercise", "")
        wt = w.get("weight_kg", 0)
        if wt > 0: exercise_maxes.setdefault(ex, []).append(wt)

    for ex, wts in exercise_maxes.items():
        if len(wts) >= 2 and wts[-1] > wts[-2] and wts[-1] >= max(wts):
            alerts.append({
                "category": "progress", "priority": 3,
                "title": f"🏆 Progressive Overload: {ex}",
                "message": f"Your working weight on {ex} went up to {wts[-1]:.1f} kg!",
                "action": "Great work adding weight to the bar. Consistency pays off.",
            })

    # ── Measurement / fat-loss alerts ────────────────────────────────────────
    if len(recent_measurements) >= 2:
        first = recent_measurements[0]
        last  = recent_measurements[-1]
        waist_change = (last.get("waist_cm") or 0) - (first.get("waist_cm") or 0)

        if waist_change > 2 and goal == "fat_loss":
            alerts.append({
                "category": "progress", "priority": 1,
                "title": "⚠️ Waist Circumference Increasing",
                "message": f"Your waist has grown by {waist_change:.1f} cm despite a fat-loss goal.",
                "action": "Review your calorie intake and add 2 cardio sessions per week.",
            })
        elif waist_change < -1:
            alerts.append({
                "category": "progress", "priority": 3,
                "title": "🔥 Fat Loss Progress Detected",
                "message": f"Your waist has reduced by {abs(waist_change):.1f} cm. Keep going!",
                "action": "Maintain your current deficit and cardio routine.",
            })

    alerts.sort(key=lambda x: x["priority"])
    return alerts


# =============================================================================
# 3. WEEKLY PROGRESS SUMMARY
# =============================================================================

def generate_weekly_summary(
    nutrition_week: List[dict],
    workouts_week: List[dict],
    profile_data: Optional[dict],
) -> Dict[str, Any]:
    """Return a structured weekly summary dict."""
    target_cal  = (profile_data or {}).get("target_calories", 2000)
    target_prot = (profile_data or {}).get("target_protein_g", 150)

    if nutrition_week:
        avg_cal  = np.mean([d.get("total_calories", 0) for d in nutrition_week])
        avg_prot = np.mean([d.get("total_protein", 0)  for d in nutrition_week])
        cal_adherence  = min(100, avg_cal  / target_cal  * 100)
        prot_adherence = min(100, avg_prot / target_prot * 100)
    else:
        avg_cal = avg_prot = cal_adherence = prot_adherence = 0

    total_volume  = sum(w.get("volume", 0) for w in workouts_week)
    session_days  = len(set(w.get("date", "") for w in workouts_week))
    muscle_groups = list(set(w.get("muscle_group", "") for w in workouts_week))

    grade = "A" if cal_adherence >= 90 and prot_adherence >= 85 and session_days >= 3 else \
            "B" if cal_adherence >= 75 and session_days >= 2 else \
            "C" if session_days >= 1 else "D"

    return {
        "avg_daily_calories":  round(avg_cal,  1),
        "avg_daily_protein":   round(avg_prot, 1),
        "calorie_adherence":   round(cal_adherence,  1),
        "protein_adherence":   round(prot_adherence, 1),
        "workout_sessions":    session_days,
        "total_volume_kg":     round(total_volume, 1),
        "muscles_trained":     muscle_groups,
        "grade":               grade,
    }


# =============================================================================
# 4. WEIGHT TREND PREDICTOR (Linear Regression)
# =============================================================================

def predict_weight_trend(weight_history: List[dict], days_ahead: int = 30) -> List[dict]:
    """
    Simple OLS linear regression on weight history.
    Returns predicted weight for the next `days_ahead` days.
    """
    if len(weight_history) < 3:
        return []

    # Build arrays: x = days since first entry, y = weight
    dates   = [w["date"] for w in weight_history]
    weights = [w["weight_kg"] for w in weight_history]

    from datetime import datetime
    base = datetime.strptime(dates[0], "%Y-%m-%d")
    x = np.array([(datetime.strptime(d, "%Y-%m-%d") - base).days for d in dates], dtype=float)
    y = np.array(weights, dtype=float)

    # Exponentially weighted least squares
    # Give more importance (weight) to recent days. Half-life = 14 days.
    w = np.exp((x - x[-1]) / 14.0)

    # Least squares fit: y = m*x + b
    m, b = np.polyfit(x, y, 1, w=w)

    # Predict forward
    last_day = int(x[-1])
    predictions = []
    for i in range(1, days_ahead + 1):
        future_day  = last_day + i
        future_date = (base + timedelta(days=future_day)).strftime("%Y-%m-%d")
        predicted   = round(float(m * future_day + b), 2)
        predictions.append({"date": future_date, "predicted_weight": predicted})

    return predictions


# =============================================================================
# 5. CALORIE & MACRO BUDGET REMAINING (real-time)
# =============================================================================

def get_nutrition_budget(profile_data: dict, today_totals: dict) -> dict:
    """Calculate remaining calories / macros for the day."""
    target_cal  = profile_data.get("target_calories",  2000)
    target_prot = profile_data.get("target_protein_g", 150)
    target_carbs = profile_data.get("target_carbs_g",  250)
    target_fat  = profile_data.get("target_fat_g",     65)

    consumed_cal  = today_totals.get("total_calories", 0)
    consumed_prot = today_totals.get("total_protein",  0)
    consumed_carb = today_totals.get("total_carbs",    0)
    consumed_fat  = today_totals.get("total_fat",      0)

    return {
        "calories": {"target": target_cal,  "consumed": consumed_cal,
                     "remaining": target_cal - consumed_cal,
                     "pct": min(100, consumed_cal / target_cal * 100) if target_cal else 0},
        "protein":  {"target": target_prot, "consumed": consumed_prot,
                     "remaining": target_prot - consumed_prot,
                     "pct": min(100, consumed_prot / target_prot * 100) if target_prot else 0},
        "carbs":    {"target": target_carbs, "consumed": consumed_carb,
                     "remaining": target_carbs - consumed_carb,
                     "pct": min(100, consumed_carb / target_carbs * 100) if target_carbs else 0},
        "fat":      {"target": target_fat,  "consumed": consumed_fat,
                     "remaining": target_fat - consumed_fat,
                     "pct": min(100, consumed_fat / target_fat * 100) if target_fat else 0},
    }
