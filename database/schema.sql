-- =============================================================================
-- database/schema.sql
-- FitX Pro — SQLite Schema Reference
-- (SQLAlchemy creates these automatically via create_tables())
-- =============================================================================

-- ── Users ─────────────────────────────────────────────────────────────────
CREATE TABLE users (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    email            TEXT UNIQUE NOT NULL,
    username         TEXT UNIQUE NOT NULL,
    hashed_password  TEXT NOT NULL,
    subscription     TEXT DEFAULT 'free' CHECK (subscription IN ('free','premium','trainer')),
    is_active        BOOLEAN DEFAULT 1,
    trainer_id       INTEGER REFERENCES users(id),
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ── User Profiles ─────────────────────────────────────────────────────────
CREATE TABLE user_profiles (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name             TEXT,
    age              INTEGER,
    gender           TEXT CHECK (gender IN ('male','female','other')),
    height_cm        REAL,
    weight_kg        REAL,
    activity_level   TEXT CHECK (activity_level IN ('sedentary','light','moderate','very_active','super_active')),
    fitness_goal     TEXT CHECK (fitness_goal IN ('fat_loss','muscle_gain','maintenance')),
    -- Calculated fields (updated on save)
    bmi              REAL,
    bmr              REAL,
    tdee             REAL,
    target_calories  INTEGER,
    target_protein_g REAL,
    target_carbs_g   REAL,
    target_fat_g     REAL,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ── Nutrition Logs ────────────────────────────────────────────────────────
CREATE TABLE nutrition_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date       TEXT NOT NULL,          -- YYYY-MM-DD
    food_name  TEXT NOT NULL,
    quantity_g REAL NOT NULL,
    meal_type  TEXT DEFAULT 'lunch',
    calories   REAL NOT NULL,
    protein_g  REAL DEFAULT 0,
    carbs_g    REAL DEFAULT 0,
    fat_g      REAL DEFAULT 0,
    logged_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_nutrition_user_date ON nutrition_logs(user_id, date);

-- ── Workout Logs ──────────────────────────────────────────────────────────
CREATE TABLE workout_logs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date         TEXT NOT NULL,
    muscle_group TEXT NOT NULL,
    exercise     TEXT NOT NULL,
    sets         INTEGER DEFAULT 3,
    reps         INTEGER DEFAULT 10,
    weight_kg    REAL DEFAULT 0,
    volume       REAL DEFAULT 0,      -- sets × reps × weight
    notes        TEXT,
    logged_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_workout_user_date ON workout_logs(user_id, date);

-- ── Body Measurements ─────────────────────────────────────────────────────
CREATE TABLE body_measurements (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date         TEXT NOT NULL,
    chest_cm     REAL,
    biceps_cm    REAL,
    waist_cm     REAL,
    thigh_cm     REAL,
    shoulders_cm REAL,
    logged_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ── Weight Logs ───────────────────────────────────────────────────────────
CREATE TABLE weight_logs (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date      TEXT NOT NULL,
    weight_kg REAL NOT NULL,
    logged_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ── AI Insights ───────────────────────────────────────────────────────────
CREATE TABLE ai_insights (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date       TEXT NOT NULL,
    category   TEXT,
    priority   INTEGER DEFAULT 2,    -- 1=high 2=medium 3=positive
    title      TEXT,
    message    TEXT,
    action     TEXT,
    is_read    BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ── Food Reference ────────────────────────────────────────────────────────
CREATE TABLE foods (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    name              TEXT UNIQUE NOT NULL,
    calories_per_100g REAL,
    protein_per_100g  REAL,
    carbs_per_100g    REAL,
    fat_per_100g      REAL,
    category          TEXT
);
