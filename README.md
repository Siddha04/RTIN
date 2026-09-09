# INSPECT-AI

Smart Real-Time Monitoring & Inspection System for SIH 26095.

Built from the Team STARKCORE proposal: mobile inspection, AI anomaly detection, 0-100 risk scoring, risk-based inspection, GPS/timestamp/evidence verification, real-time government monitoring, offline field capture and reporting.

## Stack
- Mobile: Expo React Native
- Backend: Python + FastAPI
- AI: Python + scikit-learn Isolation Forest
- Web: Vite + JavaScript
- Data target: PostgreSQL
- Maps: OpenStreetMap
- Evidence integrity: SHA-256

## Run

### API
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r services/api/requirements.txt
uvicorn services.api.app.main:app --reload --port 8000
```

### Web
```bash
cd apps/web
npm install
npm run dev
```

### Mobile
```bash
cd apps/mobile
npm install
npx expo start
```

### PostgreSQL
```bash
docker compose -f infra/docker-compose.yml up -d
```

## Demo accounts
- Ministry: `admin@inspect-ai.local` / `Admin@123`
- Inspector: `inspector@inspect-ai.local` / `Inspector@123`
- NGO/Institute: `ngo@inspect-ai.local` / `Ngo@123`

## Risk bands
- 0-30: LOW - normal monitoring
- 31-60: MEDIUM - more frequent inspection
- 61-100: HIGH - priority / surprise inspection

The proposal identifies Isolation Forest as the foundational anomaly-detection approach and describes the target workflow as Analyze -> Detect -> Prioritize -> Inspect -> Verify -> Monitor.