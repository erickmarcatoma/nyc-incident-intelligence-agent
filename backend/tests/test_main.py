from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_briefing_returns_fixture_contract() -> None:
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
    assert body["data_source"] == "fixture"
    assert body["incidents"][0]["id"] == "FIXTURE-001"
    assert body["incidents"][0]["reported_at"] == "2026-10-08T07:15:00-04:00"
    assert body["incidents"][0]["source_url"] is None
    assert "not a real incident" in body["incidents"][0]["location"]
    assert "No 511NY request was made" in body["limitations"]


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
    expected_statuses = {
        "Manhattan": "data_unavailable",
        "Brooklyn": "no_results",
        "Queens": "success",
        "Bronx": "model_unavailable",
        "Staten Island": "data_unavailable",
    }

    for borough, expected_status in expected_statuses.items():
        response = client.post(
            "/api/briefing",
            json={"borough": borough, "question": "Any fixture incidents?"},
        )
        assert response.status_code == 200
        assert response.json()["borough"] == borough
        assert response.json()["status"] == expected_status


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
