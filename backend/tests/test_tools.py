from typing import Any

import httpx
import pytest

from backend import tools
from backend.tools import IncidentDataUnavailableError, query_nyc_open_data_incidents


def collision_record(**overrides: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "collision_id": "4905715",
        "crash_date": "2026-06-11T00:00:00.000",
        "crash_time": "6:30",
        "borough": "QUEENS",
        "on_street_name": "QUEENS BLVD",
        "cross_street_name": "MAIN ST",
        "off_street_name": None,
        "latitude": "40.7282",
        "longitude": "-73.7949",
        "number_of_persons_injured": "2",
        "number_of_persons_killed": "0",
    }
    record.update(overrides)
    return record


class FakeResponse:
    def __init__(self, payload: Any) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Any:
        return self.payload


def test_query_maps_real_dataset_fields_and_requests_selected_borough(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_get(url: str, **kwargs: Any) -> FakeResponse:
        captured["url"] = url
        captured.update(kwargs)
        return FakeResponse([collision_record()])

    monkeypatch.setattr(tools.httpx, "get", fake_get)
    monkeypatch.setenv("NYC_OPEN_DATA_APP_TOKEN", "test-token")

    result = query_nyc_open_data_incidents("Queens")

    assert captured["url"] == tools.DATASET_URL
    assert captured["params"]["$where"] == "borough = 'QUEENS'"
    assert captured["params"]["$order"] == "crash_date DESC, crash_time DESC"
    assert captured["params"]["$limit"] == "50"
    assert captured["timeout"] == tools.REQUEST_TIMEOUT_SECONDS
    assert captured["headers"] == {"X-App-Token": "test-token"}
    assert result["status"] == "success"
    assert result["borough"] == "Queens"
    assert result["data_source"] == "nyc_open_data"
    incident = result["incidents"][0]
    assert incident["id"] == "4905715"
    assert incident["location"] == "QUEENS BLVD, MAIN ST"
    assert incident["reported_at"] == "2026-06-11T06:30:00-04:00"
    assert incident["reported_status"] == (
        "Reported persons injured: 2; persons killed: 0."
    )
    assert incident["source"] == "NYC Open Data: Motor Vehicle Collisions - Crashes"
    assert incident["source_url"] == (
        "https://data.cityofnewyork.us/resource/h9gi-nx95.json?collision_id=4905715"
    )
    assert "not a real-time traffic feed" in result["data_freshness"]
    assert "Publication may lag" in result["limitations"]


def test_query_sorts_records_by_parsed_local_timestamp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    earlier = collision_record(collision_id="earlier", crash_time="6:30")
    later = collision_record(collision_id="later", crash_time="11:30")
    monkeypatch.setattr(
        tools.httpx,
        "get",
        lambda *args, **kwargs: FakeResponse([earlier, later]),
    )

    result = query_nyc_open_data_incidents("Queens")

    assert [incident["id"] for incident in result["incidents"]] == [
        "later",
        "earlier",
    ]
    assert result["incidents"][0]["reported_at"] == "2026-06-11T11:30:00-04:00"
    assert "June 11, 2026 11:30 AM" in result["data_freshness"]


def test_query_reports_no_results_without_claiming_borough_is_clear(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        tools.httpx,
        "get",
        lambda *args, **kwargs: FakeResponse([]),
    )

    result = query_nyc_open_data_incidents("Brooklyn")

    assert result["status"] == "no_results"
    assert result["borough"] == "Brooklyn"
    assert result["data_source"] == "nyc_open_data"
    assert "no matching collision records" in result["message"]


def test_query_reports_source_failure_without_falling_back_to_fixtures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_get(*args: Any, **kwargs: Any) -> FakeResponse:
        raise httpx.ConnectError("network unavailable")

    monkeypatch.setattr(tools.httpx, "get", fail_get)

    with pytest.raises(IncidentDataUnavailableError, match="could not be reached"):
        query_nyc_open_data_incidents("Queens")


def test_query_rejects_unusable_dataset_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        tools.httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            [{"collision_id": "4905715", "borough": "QUEENS"}]
        ),
    )

    with pytest.raises(IncidentDataUnavailableError, match="missing required field"):
        query_nyc_open_data_incidents("Queens")


def test_query_rejects_records_outside_selected_borough(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        tools.httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            [collision_record(borough="BROOKLYN")]
        ),
    )

    with pytest.raises(
        IncidentDataUnavailableError, match="outside the requested borough"
    ):
        query_nyc_open_data_incidents("Queens")


def test_query_rejects_unexpected_response_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        tools.httpx,
        "get",
        lambda *args, **kwargs: FakeResponse({"results": [collision_record()]}),
    )

    with pytest.raises(
        IncidentDataUnavailableError, match="unexpected response format"
    ):
        query_nyc_open_data_incidents("Queens")


def test_query_preserves_missing_counts_and_uses_coordinates_for_location(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        tools.httpx,
        "get",
        lambda *args, **kwargs: FakeResponse(
            [
                collision_record(
                    on_street_name=None,
                    cross_street_name=None,
                    latitude="40.7282",
                    longitude="-73.7949",
                    number_of_persons_injured=None,
                    number_of_persons_killed=None,
                )
            ]
        ),
    )

    result = query_nyc_open_data_incidents("Queens")

    incident = result["incidents"][0]
    assert incident["location"] == "Near latitude 40.7282, longitude -73.7949"
    assert incident["reported_status"] == (
        "Reported persons injured: not reported; persons killed: not reported."
    )


def test_query_omits_app_token_when_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_get(url: str, **kwargs: Any) -> FakeResponse:
        captured.update(kwargs)
        return FakeResponse([collision_record()])

    monkeypatch.setattr(tools.httpx, "get", fake_get)
    monkeypatch.delenv("NYC_OPEN_DATA_APP_TOKEN", raising=False)

    query_nyc_open_data_incidents("Queens")

    assert captured["headers"] == {}
