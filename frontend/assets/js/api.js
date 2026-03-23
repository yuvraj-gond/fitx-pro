// =============================================================================
// frontend/assets/js/api.js
// Centralised API client — all fetch calls go through here
// =============================================================================

const BASE = "/api";

// ── Token management ─────────────────────────────────────────────────────────
const Auth = {
  getToken: ()  => localStorage.getItem("fitx_token"),
  setToken: (t) => localStorage.setItem("fitx_token", t),
  getUser:  ()  => JSON.parse(localStorage.getItem("fitx_user") || "null"),
  setUser:  (u) => localStorage.setItem("fitx_user", JSON.stringify(u)),
  clear:    ()  => { localStorage.removeItem("fitx_token"); localStorage.removeItem("fitx_user"); },
  isLoggedIn: () => !!localStorage.getItem("fitx_token"),
};

// ── Global Context Management ────────────────────────────────────────────────
const GlobalState = {
  get: (key) => JSON.parse(localStorage.getItem(`fitx_state_${key}`) || 'null'),
  set: (key, val) => localStorage.setItem(`fitx_state_${key}`, JSON.stringify(val)),
  remove: (key) => localStorage.removeItem(`fitx_state_${key}`)
};

// ── Core fetch wrapper ────────────────────────────────────────────────────────
async function api(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const token = Auth.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    if (data.detail) {
      msg = Array.isArray(data.detail) ? data.detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join(', ') : data.detail;
    }
    throw new Error(msg);
  }
  return data;
}

// ── Auth endpoints ────────────────────────────────────────────────────────────
const AuthAPI = {
  register: (payload) => api("/auth/register", { method: "POST", body: payload, auth: false }),
  login:    (payload) => api("/auth/login",    { method: "POST", body: payload, auth: false }),
  me:       ()        => api("/auth/me"),
};

// ── Profile ───────────────────────────────────────────────────────────────────
const ProfileAPI = {
  get:    ()      => api("/profile"),
  upsert: (data)  => api("/profile", { method: "PUT", body: data }),
};

// ── Nutrition ─────────────────────────────────────────────────────────────────
const NutritionAPI = {
  foods:       (search = "") => api(`/nutrition/foods?search=${encodeURIComponent(search)}`),
  log:         (data)        => api("/nutrition/log", { method: "POST", body: data }),
  getLogs:     (date)        => api(`/nutrition/log?date_str=${date}`),
  daily:       (date)        => api(`/nutrition/log?date_str=${date}`),
  deleteLog:   (id)          => api(`/nutrition/log/${id}`, { method: "DELETE" }),
  summary:     (date)        => api(`/nutrition/summary?date_str=${date}`),
  weekly:      ()            => api("/nutrition/weekly"),
};

// ── Workout ───────────────────────────────────────────────────────────────────
const WorkoutAPI = {
  exercises: ()     => api("/workout/exercises"),
  exerciseHistory: (name) => api('/workout/exercise-history/' + encodeURIComponent(name)),
  log:       (data) => api("/workout/log", { method: "POST", body: data }),
  getLogs:   (date) => api(`/workout/log?date_str=${date}`),
  daily:     (date) => api(`/workout/log?date_str=${date}`),
  deleteLog: (id)   => api(`/workout/log/${id}`, { method: "DELETE" }),
  stats:     ()     => api("/workout/stats"),
  streak:    ()     => api("/workout/streak"),
};

// ── Insights ──────────────────────────────────────────────────────────────────
const InsightsAPI = {
  get:           (refresh = false) => api(`/insights?refresh=${refresh}`),
  markRead:      (id)              => api(`/insights/${id}/read`, { method: "PATCH" }),
  weeklySummary: ()                => api("/insights/weekly-summary"),
  weightPred:    ()                => api("/insights/weight-prediction"),
  budget:        ()                => api("/insights/budget"),
};

// ── Measurements + Weight ─────────────────────────────────────────────────────
const MeasAPI = {
  get:  ()     => api("/measurements"),
  add:  (data) => api("/measurements", { method: "POST", body: data }),
};

const WeightAPI = {
  get:  ()     => api("/weight"),
  add:  (data) => api("/weight", { method: "POST", body: data }),
};

// ── Toast notifications ───────────────────────────────────────────────────────
function toast(msg, type = "info") {
  const el = document.createElement("div");
  el.className = `toast toast-${type}`;
  el.textContent = msg;
  document.body.appendChild(el);
  requestAnimationFrame(() => el.classList.add("show"));
  setTimeout(() => { el.classList.remove("show"); setTimeout(() => el.remove(), 350); }, 3500);
}

// ── Route guard ───────────────────────────────────────────────────────────────
function requireAuth() {
  if (!Auth.isLoggedIn()) {
    window.location.href = "/pages/login.html";
    return false;
  }
  return true;
}

function redirectIfLoggedIn() {
  if (Auth.isLoggedIn()) {
    window.location.href = "/pages/dashboard.html";
  }
}
