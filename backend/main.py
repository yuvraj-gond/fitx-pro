# =============================================================================
# backend/main.py
# FastAPI application entry point
# Run: uvicorn backend.main:app --reload
# =============================================================================

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .models.database import create_tables, SessionLocal
from .services.seed import seed_foods
from .routers import auth, profile, nutrition, workout, insights, trainer

# ── App init ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="FitX Pro API",
    description="Production-ready AI Fitness Tracker backend",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── CORS — allow frontend dev server + same-origin ──────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5500",
                   "http://127.0.0.1:5500", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup: create tables + seed data ──────────────────────────────────────
@app.on_event("startup")
def on_startup():
    create_tables()
    db = SessionLocal()
    try:
        seed_foods(db)
    finally:
        db.close()

# ── Register routers ─────────────────────────────────────────────────────────
app.include_router(auth.router,              prefix="/api")
app.include_router(profile.router,           prefix="/api")
app.include_router(nutrition.router,         prefix="/api")
app.include_router(workout.router,           prefix="/api")
app.include_router(insights.router,          prefix="/api")
app.include_router(insights.meas_router,     prefix="/api")
app.include_router(insights.weight_router,   prefix="/api")
app.include_router(trainer.router,           prefix="/api")

# ── Serve frontend static files ──────────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")
    app.mount("/pages",  StaticFiles(directory=os.path.join(FRONTEND_DIR, "pages")),  name="pages")

    @app.get("/", include_in_schema=False)
    def serve_root():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/pages/login.html")

    @app.get("/sw.js", include_in_schema=False)
    def serve_sw():
        return FileResponse(os.path.join(FRONTEND_DIR, "sw.js"), media_type="application/javascript")

    @app.get("/manifest.json", include_in_schema=False)
    def serve_manifest():
        return FileResponse(os.path.join(FRONTEND_DIR, "manifest.json"), media_type="application/manifest+json")

# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["System"])
def health():
    return {"status": "ok", "version": "2.0.0"}
    
