# 💪 FitX Pro — Production-Ready AI Fitness Tracker

A full-stack web application with **FastAPI backend**, **SQLite database**, and **vanilla JS frontend** — production-quality, modular, and ready to monetise.

---

## 🏗️ Architecture Overview

```
FitX-Pro/
├── backend/                    ← FastAPI Python backend
│   ├── main.py                 ← App entry point + router registration
│   ├── requirements.txt
│   ├── models/
│   │   ├── database.py         ← SQLAlchemy ORM models + DB init
│   │   └── schemas.py          ← Pydantic v2 request/response schemas
│   ├── services/
│   │   ├── auth.py             ← JWT auth, password hashing, dependencies
│   │   ├── ai_engine.py        ← AI calculations: TDEE, alerts, prediction
│   │   └── seed.py             ← Food database seeder
│   └── routers/
│       ├── auth.py             ← POST /auth/register, /auth/login
│       ├── profile.py          ← GET/PUT /profile
│       ├── nutrition.py        ← /nutrition/foods, /log, /summary, /weekly
│       ├── workout.py          ← /workout/log, /stats, /streak
│       ├── insights.py         ← /insights, /measurements, /weight
│       └── trainer.py          ← /trainer/clients (trainer tier only)
│
├── frontend/
│   ├── assets/
│   │   ├── css/main.css        ← Global dark theme stylesheet
│   │   └── js/
│   │       ├── api.js          ← Centralised fetch API client
│   │       └── shell.js        ← Sidebar + topbar injector
│   └── pages/
│       ├── login.html          ← Auth page (login + register)
│       ├── dashboard.html      ← Main overview with charts
│       ├── nutrition.html      ← Food logging + macro charts
│       ├── workout.html        ← Workout logging + analytics
│       ├── insights.html       ← AI alerts + weekly summary + weight prediction
│       ├── body.html           ← Body measurements + radar chart
│       └── profile.html        ← User profile + subscription
│
└── database/
    ├── schema.sql              ← SQL reference schema
    └── fitx.db                 ← Auto-created on first run (SQLite)
```

---

## 🚀 Setup Instructions

### 1. Clone the project

```bash
git clone <repo-url>
cd FitX-Pro
```

### 2. Set up the Python backend

```bash
cd backend
python -m venv venv

# Linux/Mac:
source venv/bin/activate

# Windows:
venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Run the FastAPI server

```bash
# From the FitX-Pro/ root directory:
uvicorn backend.main:app --reload --port 8000
```

The server starts at **http://localhost:8000**

- API docs: **http://localhost:8000/api/docs** (Swagger UI)
- ReDoc:    **http://localhost:8000/api/redoc**

### 4. Open the frontend

Since FastAPI serves the frontend, open:

**http://localhost:8000/pages/login.html**

Or use a separate dev server (e.g. VS Code Live Server on port 5500):

```bash
# The CORS config allows localhost:5500 out of the box
```

---

## 🔑 API Endpoints

### Authentication
| Method | Endpoint             | Auth | Description          |
|--------|----------------------|------|----------------------|
| POST   | /api/auth/register   | —    | Create account       |
| POST   | /api/auth/login      | —    | Login + get JWT      |
| GET    | /api/auth/me         | ✓    | Current user info    |

### Profile
| Method | Endpoint     | Description           |
|--------|--------------|-----------------------|
| GET    | /api/profile | Get profile + targets |
| PUT    | /api/profile | Create/update profile |

### Nutrition
| Method | Endpoint                          | Description           |
|--------|-----------------------------------|-----------------------|
| GET    | /api/nutrition/foods?search=      | Search food database  |
| POST   | /api/nutrition/log                | Log a food entry      |
| GET    | /api/nutrition/log?date_str=      | Get logs for a date   |
| DELETE | /api/nutrition/log/{id}           | Delete entry          |
| GET    | /api/nutrition/summary?date_str=  | Daily macro summary   |
| GET    | /api/nutrition/weekly             | Last 7 days data      |

### Workout
| Method | Endpoint                   | Description          |
|--------|----------------------------|----------------------|
| GET    | /api/workout/exercises     | Exercise list by group |
| POST   | /api/workout/log           | Log a set            |
| GET    | /api/workout/log?date_str= | Get logs for a date  |
| DELETE | /api/workout/log/{id}      | Delete entry         |
| GET    | /api/workout/stats         | 30-day stats         |
| GET    | /api/workout/streak        | Current streak       |

### AI Insights
| Method | Endpoint                          | Description               |
|--------|-----------------------------------|---------------------------|
| GET    | /api/insights?refresh=true        | Smart alerts (regenerate) |
| PATCH  | /api/insights/{id}/read           | Mark as read              |
| GET    | /api/insights/weekly-summary      | Weekly performance grade  |
| GET    | /api/insights/weight-prediction   | 30-day weight prediction  |
| GET    | /api/insights/budget              | Today's macro budget      |

### Body Data
| Method | Endpoint         | Description              |
|--------|------------------|--------------------------|
| GET    | /api/measurements | Get all measurements    |
| POST   | /api/measurements | Log new measurement     |
| GET    | /api/weight       | Weight history          |
| POST   | /api/weight       | Log today's weight      |

### Trainer (trainer tier only)
| Method | Endpoint                          | Description           |
|--------|-----------------------------------|-----------------------|
| GET    | /api/trainer/clients              | List clients          |
| GET    | /api/trainer/clients/{id}/summary | Client weekly summary |

---

## 🧠 AI Engine Details

**File:** `backend/services/ai_engine.py`

### 1. Nutrition Targets (`calculate_nutrition_targets`)
- Uses **Mifflin-St Jeor equation** for BMR (most accurate for modern populations)
- Applies activity multipliers (1.2 → 1.9)
- Goal-based calorie adjustment: Fat Loss −500, Muscle Gain +300, Maintenance ±0
- Protein: 2.2g/kg (fat loss), 2.0g/kg (muscle gain), 1.6g/kg (maintenance)

### 2. Smart Alerts (`generate_daily_alerts`)
Rule-based engine that checks:
- Calorie intake vs target (>115% = exceeded, <60% = severe under-eating)
- Protein intake vs target (<70% triggers low protein alert)
- Muscle groups not trained in 14 days
- Volume stagnation (same weight 3+ sessions)
- Waist circumference trends vs goal

### 3. Weekly Summary (`generate_weekly_summary`)
- Averages daily calories/protein
- Calculates adherence % vs targets
- Grades performance: A/B/C/D

### 4. Weight Prediction (`predict_weight_trend`)
- **Ordinary Least Squares linear regression** (NumPy polyfit)
- Trained on historical weight entries
- Predicts 30 days forward
- Requires ≥3 data points

---

## 🔐 Authentication System

- **JWT tokens** (7-day expiry) — stored in localStorage
- **bcrypt** password hashing via passlib
- `get_current_user` FastAPI dependency — used in all protected routes
- `require_premium` dependency — gates AI insights
- `require_trainer` dependency — gates trainer dashboard
- Token automatically included in all API requests via `api.js`

---

## 💼 Business / Subscription Model

### Tier Structure
| Feature                  | Free | Premium | Trainer |
|--------------------------|------|---------|---------|
| Profile + calorie tracking | ✅ | ✅ | ✅ |
| Workout logging          | ✅   | ✅      | ✅      |
| Basic dashboard          | ✅   | ✅      | ✅      |
| AI Smart Alerts          | 🔒   | ✅      | ✅      |
| Weekly summaries         | 🔒   | ✅      | ✅      |
| Weight prediction        | 🔒   | ✅      | ✅      |
| Client management        | 🔒   | 🔒      | ✅      |
| Monitor client progress  | 🔒   | 🔒      | ✅      |

### To monetise
1. Integrate Razorpay / Stripe webhooks in `/api/billing`
2. On payment success, update `user.subscription` in DB
3. All feature gates already wired via `require_premium` dependency

---

## 🌐 Deployment

### Option A — Single server (Gunicorn + Nginx)

```bash
pip install gunicorn
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

```nginx
# /etc/nginx/sites-available/fitx
server {
    listen 80;
    server_name yourdomain.com;
    location / { proxy_pass http://127.0.0.1:8000; }
}
```

### Option B — Railway / Render (1-click)

```bash
# Procfile
web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Add environment variable:
```
DATABASE_URL=sqlite:///./database/fitx.db
```

### Option C — Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🔧 Environment Variables

| Variable       | Default                        | Description              |
|----------------|--------------------------------|--------------------------|
| `DATABASE_URL` | `sqlite:///./database/fitx.db` | Database connection URL  |
| `SECRET_KEY`   | `fitx-secret-…`               | JWT signing key (CHANGE!) |

---

## 📦 Dependencies

```
fastapi          — Web framework
uvicorn          — ASGI server
sqlalchemy       — ORM
pydantic         — Data validation
python-jose      — JWT tokens
passlib[bcrypt]  — Password hashing
numpy            — ML calculations
scikit-learn     — (available for future ML features)
```

Frontend uses **zero npm packages** — pure HTML/CSS/JS with:
- Chart.js 4.4 (CDN)
- Google Fonts: Barlow Condensed + DM Sans

---

## 🏁 Quick Test

```bash
# Register a user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","username":"testuser","password":"test123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123"}'

# Use the token from login in subsequent requests:
# -H "Authorization: Bearer <token>"
```

---

*FitX Pro — Built as a portfolio + real startup project. Clean architecture, extensible, production-ready.*
