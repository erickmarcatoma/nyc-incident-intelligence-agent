from typing import Any

import pytest
from fastapi.testclient import TestClient

from backend import main
from backend.agent import AgentProtocolError, AgentUnavailableError
from backend.main import app
from backend.schemas import Borough
from backend.tools import IncidentDataUnavailableError


client = TestClient(app)


def live_result(borough: Borough) -> dict[str, Any]:
    return {
        "status": "success",
        "borough": borough.value,
        "data_source": "nyc_open_data",
        "overview": "One reported collision record was returned.",
        "incidents": [
            {
                "id": "4905715",
                "location": "QUEENS BLVD, MAIN ST",
                "type": "Motor vehicle collision",
                "reported_status": (
                    "Reported persons injured: 2; persons killed: 0."
                ),
                "reported_at": "2026-06-11T06:30:00-04:00",
                "source": "NYC Open Data: Motor Vehicle Collisions - Crashes",
                "source_url": (
                    "https://data.cityofnewyork.us/resource/"
                    "h9gi-nx95.json?collision_id=4905715"
                ),
            }
        ],
        "potential_impacts": "This historical record does not show current traffic.",
        "data_freshness": "Most recent record returned: June 11, 2026.",
        "limitations": "Historical NYC Open Data crash records, not real-time traffic.",
    }


@pytest.fixture(autouse=True)
def use_test_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        main,
        "run_agent",
        lambda question, borough: live_result(borough),
    )


def test_briefing_returns_nyc_open_data_contract() -> None:
    response = client.post(
        "/api/briefing",
        json={
            "borough": "Queens",
            "question": "What traffic incidents are affecting Queens?",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["borough"] == "Queens"
    assert body["data_source"] == "nyc_open_data"
    assert body["incidents"][0]["id"] == "4905715"
    assert body["incidents"][0]["reported_at"] == "2026-06-11T06:30:00-04:00"
    assert body["incidents"][0]["source_url"].startswith(
        "https://data.cityofnewyork.us/"
    )


def test_briefing_rejects_invalid_borough_and_blank_question() -> None:
    invalid_borough = client.post(
        "/api/briefing",
        json={"borough": "Albany", "question": "Any incidents?"},
    )
    blank_question = client.post(
        "/api/briefing",
        json={"borough": "Queens", "question": "   "},
    )

    assert invalid_borough.status_code == 422
    assert blank_question.status_code == 422


def test_briefing_accepts_every_contract_borough() -> None:
    for borough in Borough:
        response = client.post(
            "/api/briefing",
            json={"borough": borough.value, "question": "Any crash reports?"},
        )
        assert response.status_code == 200
        assert response.json()["borough"] == borough.value
        assert response.json()["data_source"] == "nyc_open_data"


def test_frontend_development_origin_can_call_api() -> None:
    response = client.options(
        "/api/briefing",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_frontend_origins_can_be_configured_without_wildcards(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "FRONTEND_ORIGINS",
        "https://app.example.com, https://admin.example.com, ",
    )

    assert main._frontend_origins() == [
        "https://app.example.com",
        "https://admin.example.com",
    ]


def test_empty_frontend_origins_do_not_enable_cross_origin_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FRONTEND_ORIGINS", "")

    assert main._frontend_origins() == []


def test_health_check_returns_ok() -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_briefing_passes_question_and_borough_to_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called_with: list[tuple[str, str]] = []

    def fake_agent(question: str, borough: Borough) -> dict[str, Any]:
        called_with.append((question, borough.value))
        return live_result(borough)

    monkeypatch.setattr(main, "run_agent", fake_agent)
    response = client.post(
        "/api/briefing",
        json={"borough": "Queens", "question": "Any major delays?"},
    )

    assert response.status_code == 200
    assert called_with == [("Any major delays?", "Queens")]


def test_agent_failure_returns_model_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_agent(question: str, borough: Borough) -> dict[str, Any]:
        raise AgentUnavailableError

    monkeypatch.setattr(main, "run_agent", fail_agent)
    response = client.post(
        "/api/briefing",
        json={"borough": "Queens", "question": "Any incidents?"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "model_unavailable",
        "borough": "Queens",
        "data_source": None,
        "message": (
            "The briefing model is currently unavailable. Please try again later."
        ),
    }


def test_invalid_agent_briefing_returns_model_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_agent(question: str, borough: Borough) -> dict[str, Any]:
        raise AgentProtocolError("The generated briefing was unsupported.")

    monkeypatch.setattr(main, "run_agent", fail_agent)
    response = client.post(
        "/api/briefing",
        json={"borough": "Queens", "question": "Any incidents?"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "model_unavailable"
    assert response.json()["message"] == (
        "The briefing model is currently unavailable. Please try again later."
    )


def test_data_source_failure_returns_data_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_agent(question: str, borough: Borough) -> dict[str, Any]:
        raise IncidentDataUnavailableError

    monkeypatch.setattr(main, "run_agent", fail_agent)
    response = client.post(
        "/api/briefing",
        json={"borough": "Queens", "question": "Any collision reports?"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "data_unavailable"
    assert response.json()["data_source"] == "nyc_open_data"
