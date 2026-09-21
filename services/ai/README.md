# INSPECT-AI AI Engine — Phase 1

## Objective

Phase 1 establishes a reproducible ML foundation for institutional anomaly detection without relying on a hidden or hard-coded synthetic training table.

## Model contract

The canonical features are:

1. attendance_rate
2. beneficiary_count
3. inspection_count
4. report_variance
5. capacity_utilization

The anomaly model is an IsolationForest trained on a caller-supplied peer cohort. The model does not invent or silently import training observations.

The engine also reports a robust median/MAD peer-deviation signal. A small transparent guardrail layer is retained for cold-start operation and major reporting discrepancies.

## Cold-start behavior

When fewer than 8 peer observations are available, the engine does not claim that Isolation Forest was trained. It returns model_status=INSUFFICIENT_REFERENCE_DATA and uses transparent guardrails only.

This is intentional. Production ML should prefer an explicit "not enough evidence to train" state over fabricated training data.

## Verification

The phase-1 unit tests verify:

- deterministic feature extraction;
- input validation;
- reference-cohort construction;
- Isolation Forest training from caller-supplied data only;
- explicit cold-start status;
- high-variance guardrails;
- no invented CCTV headcount.

## Next integration step

Phase 2 will wire the peer cohort to persisted institution/history data so API inference uses real database observations instead of the current single-record call path.
