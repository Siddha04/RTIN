from services.ai.external_context import CONTEXT_FEATURE_NAMES
from services.ai.enriched_training import ENRICHED_FEATURE_NAMES, extract_enriched_features
from services.ai.features import FEATURE_NAMES


def test_enriched_feature_contract():
    record = {
        "attendance": 70,
        "beneficiaries": 60,
        "inspections": 4,
        "report_variance": 0.03,
        "sanctioned_capacity": 80,
        "weather_temperature_c": 31,
        "weather_humidity_pct": 72,
        "weather_rainfall_24h_mm": 14,
        "weather_wind_kmph": 18,
        "weather_warning_score": 0.7,
        "udid_total_count": 12000,
        "deaddiction_centres_count": 4,
    }

    vector = extract_enriched_features(record)

    assert len(FEATURE_NAMES) == 5
    assert len(CONTEXT_FEATURE_NAMES) == 7
    assert len(ENRICHED_FEATURE_NAMES) == 12
    assert vector.shape == (12,)
    assert vector[5] == 31.0
    assert vector[-1] == 4.0


def test_missing_external_context_has_explicit_zero_defaults():
    record = {
        "attendance": 70,
        "beneficiaries": 60,
        "inspections": 4,
        "report_variance": 0.03,
        "sanctioned_capacity": 80,
    }

    vector = extract_enriched_features(record)
    assert vector.shape == (12,)
    assert float(vector[5:].sum()) == 0.0
