# RTIN External Data and Real-Data Training

RTIN does not store raw public datasets in Git.

## Data lanes

### Training context
Use public, non-sensitive aggregate datasets from the Government of India's Open Government Data platform.

Suitable context sources identified for RTIN include:
- UDID district-wise disability/age/gender aggregates.
- District-wise de-addiction-centre counts for Tamil Nadu.
- Other OGD district-level social, health and demographic aggregates selected by UUID.

These datasets are contextual features. They do not become inspection labels.

### Real-time context
Use official India Meteorological Department services for current weather, district rainfall, warnings and forecast context. IMD API access may require public-IP whitelisting.

## Storage

Raw downloads belong outside the repository.

Set RTIN_EXTERNAL_DATA_DIR to an external path such as ~/rtin-data.

The RTIN database stores normalized external observations needed for live context and training joins. Generated model artifacts remain outside Git.

## Required environment

DATAGOV_API_KEY

DATAGOV_RESOURCES

IMD_API_TOKEN is optional; IMD access can require network/public-IP authorization.

## Refresh online context

python scripts/refresh_online_data.py

For scheduled refresh, invoke the same command from the operating system scheduler. Do not run an infinite watcher inside the FastAPI web worker.

## Train the enriched model

First collect at least 20 confirmed audit outcomes in institution_metrics.outcome_label.

Then run:

python scripts/train_enriched_model.py

The enriched model uses RTIN institutional features plus district-level weather, UDID context where available, and de-addiction-centre context where available.

Public datasets are context; confirmed RTIN audit outcomes are the supervised target.

## Source attribution

Each external observation stores source and dataset metadata. OGD resources must follow the license/terms attached to the individual resource, with attribution.