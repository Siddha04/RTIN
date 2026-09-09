# INSPECT-AI — Smart Real-Time Monitoring & Inspection Mobile App (SIH 26095)

**Smart India Hackathon 2026 — Problem Statement 26095**  
*Team STARKCORE Implementation*

---

## 🏛 System Flow & Architecture

```
Institution Data ➔ Data Preprocessing ➔ AI/ML Analysis (Isolation Forest)
         ➔ Risk Score (0–100) ➔ Risk-Based Decision ➔ Priority Mobile Inspection
         ➔ SHA-256 / GPS / Timestamp Verification ➔ Centralized Government Dashboard
```

`INSPECT-AI` is an end-to-end monitoring solution for government oversight of welfare institutions, schools, and NGOs. It automatically flags record anomalies, prioritizes field audits, verifies inspector evidence integrity, and presents real-time analytics on a centralized command dashboard.

---

## 🚀 System Features

1. **AI Anomaly & Risk Engine:** Isolation Forest ML model analyzing attendance, headcount variance, and inspection history to produce a 0–100 risk score.
2. **Dynamic Risk Banding:**
   - `0–30` (LOW): Normal routine monitoring
   - `31–60` (MEDIUM): Increased audit frequency
   - `61–100` (HIGH): Priority & surprise inspections recommended
3. **Role-Based Access Control (RBAC):** `MINISTRY_ADMIN`, `INSPECTOR`, and `NGO` roles with strict JWT + server-side enforcement.
4. **Mobile Inspection App:** Expo React Native field application supporting offline inspection queueing, GPS tag capture, and checklist validation.
5. **Multi-Factor Evidence Integrity Verification:** Validates capture GPS coordinates, timestamp within 24 hours, officer session, institution ID match, and SHA-256 file checksums. Physical uploads persisted to disk storage (`uploads/`).
6. **Live Interactive Risk Map:** Leaflet OpenStreetMap view rendering institution markers color-coded by risk band.
7. **Real-time Government Dashboard:** Live metrics, active inspection tracking, alert center, and automated compliance scoring.
8. **Exportable Audit Reports:** Multi-format reporting engine supporting CSV and structured JSON exports.

---

## 🛠 Tech Stack

- **Backend API:** FastAPI, SQLAlchemy ORM, PyJWT, Python 3.12
- **AI/ML Module:** scikit-learn (Isolation Forest), NumPy
- **Frontend Dashboard:** React 19, Vite 7, TypeScript, React Router 7, Leaflet OSM
- **Mobile Application:** Expo 52, React Native, AsyncStorage, Expo Location
- **Database:** PostgreSQL (Primary Production Target) / SQLite (Local Fallback)
- **Security & Integrity:** Passwords hashed with SHA-256 PBKDF2, JWT tokens, file SHA-256 hashes

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` in the project root:

```bash
cp .env.example .env
```

Key environment configuration parameters:

```ini
# Database Connection (PostgreSQL or SQLite fallback)
DATABASE_URL=postgresql://inspect:inspect@localhost:5432/inspect_ai

# JWT Authentication
JWT_SECRET=inspect-ai-super-secret-key-26095-production-change-me
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480

# API Endpoint
API_BASE_URL=http://localhost:8000
```

---

## 📦 Setup & Execution Instructions

### 1. Database Setup (PostgreSQL)

Launch PostgreSQL container via Docker Compose:

```bash
docker compose -f infra/docker-compose.yml up -d
```

*(Note: If Docker is unavailable, the backend automatically uses a local persistent SQLite database `services/api/inspect_ai.db`)*

### 2. Backend API Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r services/api/requirements.txt pytest httpx

# Run database seed & API server
uvicorn services.api.app.main:app --reload --port 8000
```

API documentation is accessible at `http://localhost:8000/docs`.

### 3. Frontend Web Dashboard Setup

```bash
cd apps/web

# Install dependencies
npm install

# Run Vite development server
npm run dev
```

Dashboard will launch at `http://localhost:5173`.

### 4. Mobile Field App Setup

```bash
cd apps/mobile

# Install dependencies
npm install

# Start Expo development server
npx expo start
```

---

## 🧪 Testing & Verification Commands

### Run Backend Pytest Suite (27 tests)

```bash
# Set PYTHONPATH to root directory
set PYTHONPATH=.

# Run pytest with verbose output
.venv\Scripts\python.exe -m pytest -v
```

### Run Python Module Compilation Check

```bash
.venv\Scripts\python.exe -m compileall services/api services/ai
```

### Run Frontend Typecheck & Production Build

```bash
cd apps/web

# TypeScript typecheck
npx tsc --noEmit

# Production Vite build
npm run build
```

---

## 🔑 Seed User Credentials

| Role | Email | Password | Allowed Permissions |
| :--- | :--- | :--- | :--- |
| **Ministry Admin** | `admin@inspect-ai.local` | `Admin@123` | Full administrative CRUD, scheduling, alert management |
| **Field Inspector** | `inspector@inspect-ai.local` | `Inspector@123` | Inspection status updates, evidence upload & verification |
| **NGO Auditor** | `ngo@inspect-ai.local` | `Ngo@123` | Read-only analytics & reporting views (mutations blocked) |

---

## 🚀 CI/CD Pipeline

Continuous Integration is powered by GitHub Actions (`.github/workflows/ci.yml`). It executes automated typechecking, Python module compilation, pytest test runs, and Vite production bundle builds on every push to `main`.