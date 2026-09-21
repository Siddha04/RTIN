# INSPECT-AI AI Engine — Phase 5

Phase 5 replaces random inspection target/inspector selection with deterministic optimization.

## Target scoring

Target priority combines:
- stored risk score;
- anomaly flag;
- reporting variance.

## Hard constraints

- Inspector home district is never eligible.
- Inspector/institution pair is blocked during the 180-day cooling period.
- Workload is included in the assignment score.
- Ties are deterministic by stable IDs; no random choice is used.

The optimizer returns the reasons used for both target and inspector selection so the allocation is auditable.
