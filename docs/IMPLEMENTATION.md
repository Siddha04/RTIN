# INSPECT-AI implementation map

## Source requirements mapped to software

| Source requirement | Implementation |
|---|---|
| Mobile inspection | Expo React Native assignments, inspection notes, camera capture |
| AI analytics | Python Isolation Forest + risk score service |
| Risk score 0-100 | API `/api/institutions` and dashboard risk bands |
| Priority/surprise inspections | Priority status + inspection queue |
| GPS/timestamp/officer/institution verification | `/api/evidence/verify` |
| SHA-256 evidence integrity | `/api/evidence/upload` |
| Government monitoring | React dashboard with KPI cards, risk list and map |
| Offline capture | Mobile AsyncStorage queue |
| OpenStreetMap / Maps API | Leaflet + OpenStreetMap tiles |
| JWT security | Authentication contract in API with role metadata; production deployments should replace demo tokens with signed JWT issuance |

The PPT lists FastAPI, PostgreSQL, Python/scikit-learn, React and OpenStreetMap/Maps API in the technical approach, and the architecture diagram identifies a mobile inspector client, Ministry web platform, NGO/institute portal, modular backend services, AI service, PostgreSQL, object storage and external integrations.
