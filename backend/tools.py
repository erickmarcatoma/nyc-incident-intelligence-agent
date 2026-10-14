import json
from pathlib import Path
from typing import Any

from backend.schemas import (
	Borough,
	BriefingFailureResponse,
	BriefingSuccessResponse,
	DataSource,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures"
FIXTURE_PATHS = {
	Borough.MANHATTAN: FIXTURE_DIR / "data_unavailable.json",
	Borough.BRONX: FIXTURE_DIR / "model_unavailable.json",
	Borough.QUEENS: FIXTURE_DIR / "queens_success.json",
	Borough.BROOKLYN: FIXTURE_DIR / "brooklyn_empty.json",
}


def query_511ny_incidents(borough: Borough | str) -> dict[str, Any]:
	"""Return a validated fixture response; this does not call 511NY."""
	selected_borough = Borough(borough)
	fixture_path = FIXTURE_PATHS.get(selected_borough)

	if fixture_path is None:
		return BriefingFailureResponse(
			status="data_unavailable",
			borough=selected_borough,
			data_source=DataSource.FIXTURE,
			message=(
				f"No fixture is configured for {selected_borough.value}. "
				"No 511NY request was made."
			),
		).model_dump(mode="json")

	fixture_payload = json.loads(fixture_path.read_text(encoding="utf-8"))
	status = fixture_payload.get("status")

	if status == "success":
		return BriefingSuccessResponse.model_validate(fixture_payload).model_dump(
			mode="json"
		)

	return BriefingFailureResponse.model_validate(fixture_payload).model_dump(
		mode="json"
	)
