# INSPECT-AI Public-Data Training

This pipeline uses public government datasets as **context features** and uses
confirmed RTIN inspection outcomes as the supervised target.

## Public inputs

Configure the official resources through `DATAGOV_RESOURCES` and the IMD
endpoints already supported by `services/ai/online_data.py`.

Recommended sources:

- UDISE+ enrolment, teacher, and infrastructure resources:
  https://www.data.gov.in/catalog/unified-district-information-system-for-education-plus-udise-plus
- Tamil Nadu welfare-hostel resources:
  https://tn.data.gov.in/
- Mission Vatsalya / child-care resources:
  https://www.data.gov.in/
- UDID district disability resources:
  https://www.data.gov.in/resource/district-wise-disability-wise-age-group-wise-gender-wise-unique-disability-id-udid-data
- IMD real-time weather/rainfall/warnings:
  https://mausam.imd.gov.in/

Raw downloads are not committed to Git. Normalized observations are stored
in the RTIN database and model artifacts are written under `~/rtin-data`
by default.

## Training policy

Public data does **not** create a fake `outcome_label`.

The supervised target remains:

- `0`: no confirmed issue
- `1`: confirmed issue

The final enriched XGBoost model combines the five RTIN core features with
public context features.

## 90% validation gate

Training uses repeated stratified cross-validation. The default registration
gate is:

`cv_accuracy >= 0.90`

If the measured CV accuracy is below 90%, the command exits with a quality-gate
failure and no production artifact is registered.

This prevents the system from claiming 90% accuracy without evidence.

## Run

From the repository root after configuring the official public-data resource
IDs/API settings:

```powershell
py scripts/refresh_online_data.py
py scripts/train_public_enriched_model.py
```

To train from already ingested public observations:

```powershell
py scripts/train_public_enriched_model.py --skip-refresh
```

The model can only pass the gate when at least 20 confirmed RTIN outcomes are
available and both classes are present. A larger labeled history is strongly
preferred for production evaluation.
