import os
from datetime import date, datetime, time
from typing import Any
from urllib.parse import urlencode
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from dotenv import load_dotenv

from backend.schemas import (
    Borough,
    BriefingFailureResponse,
    BriefingSuccessResponse,
    DataSource,
    Incident,
)


load_dotenv()

DATASET_ID = "h9gi-nx95"
DATASET_URL = f"https://data.cityofnewyork.us/resource/{DATASET_ID}.json"
DATASET_PAGE_URL = f"https://data.cityofnewyork.us/d/{DATASET_ID}"
MAX_INCIDENTS = 50
REQUEST_TIMEOUT_SECONDS = 15


class IncidentDataUnavailableError(Exception):
    """NYC Open Data could not provide usable crash records."""


def _record_string(record: dict[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise IncidentDataUnavailableError(
            f"The NYC Open Data response is missing required field {field!r}."
        )
    return value.strip()


def _record_count(record: dict[str, Any], field: str) -> str:
    value = record.get(field)
    if value is None:
        return "not reported"
    try:
        count = int(value)
    except (TypeError, ValueError) as error:
        raise IncidentDataUnavailableError(
            f"The NYC Open Data response has an invalid {field!r} value."
        ) from error
    if count < 0:
        raise IncidentDataUnavailableError(
            f"The NYC Open Data response has an invalid {field!r} value."
        )
    return str(count)


def _reported_at(record: dict[str, Any]) -> datetime:
    crash_date = _record_string(record, "crash_date")
    crash_time = _record_string(record, "crash_time")
    try:
        local_date = date.fromisoformat(crash_date[:10])
        local_time = datetime.strptime(crash_time, "%H:%M").time()
        return datetime.combine(
            local_date, local_time, tzinfo=ZoneInfo("America/New_York")
        )
    except (ValueError, ZoneInfoNotFoundError) as error:
        raise IncidentDataUnavailableError(
            "The NYC Open Data response has an invalid crash date or time."
        ) from error


def _location(record: dict[str, Any]) -> str:
    street_names = [
        record[field].strip()
        for field in ("on_street_name", "cross_street_name", "off_street_name")
        if isinstance(record.get(field), str) and record[field].strip()
    ]
    if street_names:
        return ", ".join(dict.fromkeys(street_names))

    latitude = record.get("latitude")
    longitude = record.get("longitude")
    if latitude and longitude:
        return f"Near latitude {latitude}, longitude {longitude}"
    return "Location not reported"


def _normalize_record(record: dict[str, Any]) -> Incident:
    collision_id = _record_string(record, "collision_id")
    injured = _record_count(record, "number_of_persons_injured")
    killed = _record_count(record, "number_of_persons_killed")
    source_url = f"{DATASET_URL}?{urlencode({'collision_id': collision_id})}"

    return Incident(
        id=collision_id,
        location=_location(record),
        type="Motor vehicle collision",
        reported_status=f"Reported persons injured: {injured}; persons killed: {killed}.",
        reported_at=_reported_at(record),
        source="NYC Open Data: Motor Vehicle Collisions - Crashes",
        source_url=source_url,
    )


def query_nyc_open_data_incidents(borough: Borough | str) -> dict[str, Any]:
    """Fetch and normalize real collision records from NYC Open Data."""
    selected_borough = Borough(borough)
    headers = {}
    app_token = os.getenv("NYC_OPEN_DATA_APP_TOKEN")
    if app_token:
        headers["X-App-Token"] = app_token

    params = {
        "$where": f"borough = '{selected_borough.value.upper()}'",
        "$order": "crash_date DESC, crash_time DESC",
        "$limit": str(MAX_INCIDENTS),
        "$select": (
            "collision_id,crash_date,crash_time,borough,on_street_name,"
            "cross_street_name,off_street_name,latitude,longitude,"
            "number_of_persons_injured,number_of_persons_killed"
        ),
    }

    try:
        response = httpx.get(
            DATASET_URL,
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise IncidentDataUnavailableError(
            "NYC Open Data could not be reached or returned invalid JSON."
        ) from error

    if not isinstance(payload, list) or any(
        not isinstance(record, dict) for record in payload
    ):
        raise IncidentDataUnavailableError(
            "NYC Open Data returned an unexpected response format."
        )

    if any(
        record.get("borough") != selected_borough.value.upper()
        for record in payload
    ):
        raise IncidentDataUnavailableError(
            "NYC Open Data returned a record outside the requested borough."
        )

    if not payload:
        return BriefingFailureResponse(
            status="no_results",
            borough=selected_borough,
            data_source=DataSource.NYC_OPEN_DATA,
            message=(
                "NYC Open Data returned no matching collision records for "
                "the selected borough."
            ),
        ).model_dump(mode="json")

    incidents = sorted(
        (_normalize_record(record) for record in payload),
        key=lambda incident: incident.reported_at,
        reverse=True,
    )
    newest_record = max(incident.reported_at for incident in incidents)
    return BriefingSuccessResponse(
        borough=selected_borough,
        data_source=DataSource.NYC_OPEN_DATA,
        overview=(
            f"Retrieved {len(incidents)} NYC Open Data motor vehicle collision "
            f"records for {selected_borough.value}."
        ),
        incidents=incidents,
        potential_impacts=(
            "These historical crash records do not establish current traffic "
            "conditions or impacts."
        ),
        data_freshness=(
            "Most recent record returned: "
            f"{newest_record.strftime('%B %d, %Y %I:%M %p %Z')}. "
            "NYC Open Data publication can lag; this is not a real-time traffic feed."
        ),
        limitations=(
            f"Records are from the NYC Open Data Motor Vehicle Collisions - Crashes "
            f"dataset, limited to the {selected_borough.value} borough and the "
            f"{MAX_INCIDENTS} most recently reported crashes. Publication may lag "
            "the event date. Records and injury counts are as reported in the "
            "source and are not real-time traffic conditions. "
            f"Dataset: {DATASET_PAGE_URL}"
        ),
    ).model_dump(mode="json")
