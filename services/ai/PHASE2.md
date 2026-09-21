# INSPECT-AI AI Engine — Phase 2

Phase 2 connects the risk engine to persisted institutional observations.

## Added

- institution_metrics history table.
- Snapshot recording service.
- Peer-cohort construction from historical observations.
- Cross-scheme fallback only when the same-scheme cohort is insufficient.
- Current active institution fallback for cold start.
- Risk-analysis provenance fields: model name, version, cohort size and scope.
- API endpoints:
  - POST /api/ai/history
  - GET /api/ai/history/{institution_id}
  - POST /api/ai/analyze now uses database-backed cohort data when an institution ID is supplied.

## Data integrity rules

The target institution is excluded from its own peer cohort. The engine continues to report INSUFFICIENT_REFERENCE_DATA when the persisted dataset is too small rather than fabricating training observations.

## Verification

Phase 2 adds tests for history-table availability, feature compatibility and persisted peer-cohort inference, while the CI workflow retains Phase 1 and API regression tests.
