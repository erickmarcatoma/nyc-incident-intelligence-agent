import pytest

from backend.tools import query_511ny_incidents


def test_query_returns_validated_queens_fixture() -> None:
	result = query_511ny_incidents("Queens")

	assert result["status"] == "success"
	assert result["borough"] == "Queens"
	assert result["data_source"] == "fixture"
	assert result["incidents"][0]["id"] == "FIXTURE-001"
	assert "not a real incident" in result["incidents"][0]["location"]


def test_query_returns_brooklyn_no_results_fixture() -> None:
	result = query_511ny_incidents("Brooklyn")

	assert result == {
		"status": "no_results",
		"borough": "Brooklyn",
		"data_source": "fixture",
		"message": (
			"No matching incidents were returned by the source for the selected "
			"area and query."
		),
	}


def test_query_marks_unconfigured_fixture_unavailable() -> None:
	result = query_511ny_incidents("Manhattan")

	assert result["status"] == "data_unavailable"
	assert result["borough"] == "Manhattan"
	assert result["data_source"] == "fixture"


def test_query_returns_model_unavailable_fixture() -> None:
	result = query_511ny_incidents("Bronx")

	assert result["status"] == "model_unavailable"
	assert result["borough"] == "Bronx"
	assert result["data_source"] == "fixture"


def test_query_rejects_unknown_borough() -> None:
	with pytest.raises(ValueError):
		query_511ny_incidents("Albany")
