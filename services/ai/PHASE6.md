# INSPECT-AI AI Engine — Phase 6

Phase 6 completes the core ML lifecycle without treating unlabeled demo data as a trained supervised model.

## Model lifecycle

Institution observations -> canonical feature engineering -> dataset fingerprint -> offline model training -> versioned artifact -> SHA-256 integrity -> model status -> drift monitoring -> retraining.

## Models

Isolation Forest is used for unsupervised peer anomaly detection. Training requires at least 8 observations and preserves the five-feature inference contract.

XGBoost is the supervised binary risk model used only when confirmed audit outcomes exist. Training requires at least 20 labeled observations and both classes (0 and 1). The application never creates synthetic labels.

## Confirmed outcomes

The institution metric history stores an optional confirmed outcome label:
- 0 = no confirmed issue
- 1 = confirmed issue

Only ministry or inspector users can submit the outcome label.

## Monitoring

Population Stability Index (PSI) is calculated per canonical feature. The default configurable threshold is 0.20.

## Artifact registry

Generated model files and metadata are stored under services/api/artifacts/models/ and are ignored by Git. Metadata includes model name/version, dataset fingerprint, metrics or training statistics, feature names, artifact SHA-256, and creation timestamp.

## Training commands

python scripts/train_models.py --model isolation_forest

python scripts/train_models.py --model xgboost

The supervised command should only be used after enough confirmed audit labels have been collected.

## APIs

GET /api/ai/model/status
POST /api/ai/train
POST /api/ai/monitor/drift

NO_REGISTERED_MODEL is an expected cold-start status until a training job creates an artifact.
