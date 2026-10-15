from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from backend.agent import Borough
from backend.incident_processor import (
    AgentResponseValidationError,
    analyze_incidents,
    validate_agent_response,
)
from backend.schemas import Incident


def incident(
    collision_id: str,
    location: str,
    injuries: str,
) -> Incident:
    return Incident(
        id=collision_id,
        location=location,
        type="Motor vehicle collision",
        reported_status=(
            f"Reported persons injured: {injuries}; persons killed: 0."
        ),
        reported_at=datetime(
            2026, 6, 11, 6, 30, tzinfo=ZoneInfo("America/New_York")
        ),
        source="NYC Open Data: Motor Vehicle Collisions - Crashes",
        source_url=(
            "https://data.cityofnewyork.us/resource/"
            f"h9gi-nx95.json?collision_id={collision_id}"
        ),
    )


def test_analyze_incidents_groups_intersections_and_applies_three_injury_threshold() -> None:
    analysis = analyze_incidents(
        [
            incident("1", "QUEENS BLVD, MAIN ST", "2"),
            incident("2", "main st, queens blvd", "1"),
            incident("3", "QUEENS BLVD, 35TH ST", "2"),
            incident("4", "Near latitude 40.7, longitude -73.8", "3"),
        ]
    )

    assert analysis == {
        "incident_count": 4,
        "intersection_count": 2,
        "high_injury_threshold": 3,
        "high_injury_intersections": [
            {
                "intersection": "MAIN ST / QUEENS BLVD",
                "collision_count": 2,
                "reported_injuries": 3,
                "injury_reports_complete": True,
            }
        ],
        "unclassified_intersection_count": 0,
    }


def test_analyze_incidents_does_not_promote_unknown_counts_or_coordinates() -> None:
    analysis = analyze_incidents(
        [
            incident("1", "QUEENS BLVD, MAIN ST", "not reported"),
            incident("2", "Near latitude 40.7, longitude -73.8", "3"),
        ]
    )

    assert analysis["intersection_count"] == 1
    assert analysis["high_injury_intersections"] == []
    assert analysis["unclassified_intersection_count"] == 1


def test_validator_accepts_analysis_supported_high_injury_intersection() -> None:
    tool_result = {
        "status": "success",
        "borough": "Queens",
        "data_source": "nyc_open_data",
        "overview": "Retrieved three NYC Open Data motor vehicle collision records for Queens.",
        "incidents": [
            item.model_dump(mode="json")
            for item in [
                incident("1", "QUEENS BLVD, MAIN ST", "2"),
                incident("2", "main st, queens blvd", "1"),
                incident("3", "Queens Blvd, Main St", "0"),
            ]
        ],
        "potential_impacts": (
            "These historical crash records do not establish current traffic "
            "conditions or impacts."
        ),
        "data_freshness": "Most recent record returned: June 11, 2026.",
        "limitations": "Historical NYC Open Data crash records.",
    }

    result = validate_agent_response(
        tool_result,
        {
            "overview": (
                "One high-injury intersection has three reported injuries."
            ),
            "potential_impacts": (
                "The historical reports do not establish current traffic."
            ),
        },
        Borough.QUEENS,
    )

    assert result["overview"] == (
        "One high-injury intersection has three reported injuries."
    )


def test_validator_rejects_incorrect_high_injury_intersection_count() -> None:
    tool_result = {
        "status": "success",
        "borough": "Queens",
        "data_source": "nyc_open_data",
        "overview": "Retrieved one NYC Open Data motor vehicle collision record for Queens.",
        "incidents": [
            incident("1", "QUEENS BLVD, MAIN ST", "2").model_dump(mode="json")
        ],
        "potential_impacts": (
            "These historical crash records do not establish current traffic."
        ),
        "data_freshness": "Most recent record returned: June 11, 2026.",
        "limitations": "Historical NYC Open Data crash records.",
    }

    with pytest.raises(
        AgentResponseValidationError, match="high-injury intersections"
    ):
        validate_agent_response(
            tool_result,
            {
                "overview": "One high-injury intersection has two reported injuries.",
                "potential_impacts": (
                    "The historical reports do not establish current traffic."
                ),
            },
            Borough.QUEENS,
        )
