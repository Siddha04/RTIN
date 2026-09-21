from datetime import datetime, timezone
from types import SimpleNamespace

from services.ai.online_data import (
    _district_from_row,
    _observed_at_from_row,
    _unwrap_records,
    payload_hash,
)


def test_payload_hash_is_deterministic_for_mapping_order():
    first = {"b": 2, "a": 1}
    second = {"a": 1, "b": 2}
    assert payload_hash(first) == payload_hash(second)


def test_unwrap_records_handles_common_api_shapes():
    assert _unwrap_records([{"a": 1}]) == [{"a": 1}]
    assert _unwrap_records({"records": [{"a": 1}]}) == [{"a": 1}]
    assert _unwrap_records({"result": {"data": [{"a": 1}]}}) == [{"a": 1}]
    assert _unwrap_records({"a": 1, "b": 2}) == [{"a": 1, "b": 2}]


def test_district_normalization():
    assert _district_from_row({"District Name": "Salem"}) == "SALEM"
    assert _district_from_row({"district": "Erode"}) == "ERODE"
    assert _district_from_row({"name": "x"}) is None


def test_observed_date_parsing():
    assert _observed_at_from_row({"Date of Observation": "2026-09-22"}) == datetime(
        2026, 9, 22, tzinfo=timezone.utc
    )
    assert _observed_at_from_row({"Date": "22/09/2026"}) == datetime(
        2026, 9, 22, tzinfo=timezone.utc
    )
    assert _observed_at_from_row({"Date": "not-a-date"}) is None
