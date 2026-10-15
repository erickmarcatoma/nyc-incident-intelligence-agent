import re
from typing import Any
from urllib.parse import parse_qs, urlparse

from pydantic import ValidationError

from backend.schemas import Borough, BriefingSuccessResponse, DataSource


DATASET_HOST = "data.cityofnewyork.us"
DATASET_PATH = "/resource/h9gi-nx95.json"
DATASET_SOURCE = "NYC Open Data: Motor Vehicle Collisions - Crashes"
_NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}
_NUMBER_TOKEN = r"(?:\d+|" + "|".join(_NUMBER_WORDS) + r")"
_INCIDENT_COUNT_CLAIM = re.compile(
    rf"\b({_NUMBER_TOKEN})\s+(?:(?:reported|recorded)\s+)?"
    r"(?:motor vehicle\s+)?(?:collisions?|crashes?|incidents?|records?)\b",
    re.IGNORECASE,
)
_PERSON_COUNT_CLAIM = re.compile(
    rf"\b({_NUMBER_TOKEN})\s+(?:persons?|people|individuals?)\s+"
    r"(?:(?:were|was)\s+)?(injured|killed)\b",
    re.IGNORECASE,
)
_INJURY_COUNT_CLAIM = re.compile(
    rf"\b({_NUMBER_TOKEN})\s+(injuries|fatalities|deaths)\b",
    re.IGNORECASE,
)
_CURRENT_CONDITION_CLAIM = re.compile(
    r"\b(?:currently\s+(?:active|ongoing|closed|open|clear|congested|"
    r"affecting)|(?:is|remains)\s+(?:closed|open|clear|congested))\b",
    re.IGNORECASE,
)


class AgentResponseValidationError(ValueError):
    """The generated briefing is invalid or unsupported by its source records."""


def _number_value(value: str) -> int:
    return int(value) if value.isdigit() else _NUMBER_WORDS[value.casefold()]


def _validate_count_claims(
    text: str, briefing: BriefingSuccessResponse
) -> None:
    for match in _INCIDENT_COUNT_CLAIM.finditer(text):
        if _number_value(match.group(1)) != len(briefing.incidents):
            raise AgentResponseValidationError(
                "The briefing reports an unsupported number of incidents."
            )

    injury_counts: list[int] = []
    fatality_counts: list[int] = []
    for incident in briefing.incidents:
        counts = re.fullmatch(
            r"Reported persons injured: (\d+|not reported); "
            r"persons killed: (\d+|not reported)\.",
            incident.reported_status,
        )
        if counts is None:
            continue
        if counts.group(1) != "not reported":
            injury_counts.append(int(counts.group(1)))
        if counts.group(2) != "not reported":
            fatality_counts.append(int(counts.group(2)))

    for match in _PERSON_COUNT_CLAIM.finditer(text):
        count = _number_value(match.group(1))
        known_counts = (
            injury_counts if match.group(2).casefold() == "injured" else fatality_counts
        )
        if len(known_counts) != len(briefing.incidents) or count != sum(known_counts):
            raise AgentResponseValidationError(
                "The briefing reports an unsupported injury or fatality count."
            )

    for match in _INJURY_COUNT_CLAIM.finditer(text):
        count = _number_value(match.group(1))
        known_counts = (
            injury_counts if match.group(2).casefold() == "injuries" else fatality_counts
        )
        if len(known_counts) != len(briefing.incidents) or count != sum(known_counts):
            raise AgentResponseValidationError(
                "The briefing reports an unsupported injury or fatality count."
            )


def _supported_numbers(briefing: BriefingSuccessResponse) -> set[int]:
    supported = {len(briefing.incidents)}
    for incident in briefing.incidents:
        supported.update(
            int(value)
            for value in re.findall(r"\d+", incident.reported_status)
        )
        supported.update(int(value) for value in re.findall(r"\d+", incident.id))
        supported.update(
            int(value)
            for value in re.findall(r"\d+", incident.reported_at.isoformat())
        )
    return supported


def _validate_source_attribution(briefing: BriefingSuccessResponse) -> None:
    for incident in briefing.incidents:
        if incident.source != DATASET_SOURCE or incident.source_url is None:
            raise AgentResponseValidationError(
                "An incident is missing NYC Open Data source attribution."
            )
        source_url = urlparse(str(incident.source_url))
        if (
            source_url.hostname != DATASET_HOST
            or source_url.path != DATASET_PATH
            or parse_qs(source_url.query).get("collision_id") != [incident.id]
        ):
            raise AgentResponseValidationError(
                "An incident source link does not identify its NYC Open Data record."
            )


def _validate_generated_claims(
    generated: dict[str, Any],
    briefing: BriefingSuccessResponse,
    borough: Borough,
) -> dict[str, str]:
    if set(generated) != {"overview", "potential_impacts"} or not all(
        isinstance(generated.get(field), str) and generated[field].strip()
        for field in ("overview", "potential_impacts")
    ):
        raise AgentResponseValidationError("The model returned an invalid briefing.")

    text = " ".join(generated[field] for field in ("overview", "potential_impacts"))
    _validate_count_claims(text, briefing)
    if _CURRENT_CONDITION_CLAIM.search(text):
        raise AgentResponseValidationError(
            "The briefing makes an unsupported claim about current traffic conditions."
        )

    mentioned_boroughs = {
        name.casefold()
        for name in (name.value for name in Borough)
        if re.search(rf"\b{re.escape(name)}\b", text, re.IGNORECASE)
    }
    if mentioned_boroughs - {borough.value.casefold()}:
        raise AgentResponseValidationError(
            "The briefing mentions a borough other than the selected borough."
        )

    supported_numbers = _supported_numbers(briefing)
    claimed_numbers = {int(value) for value in re.findall(r"\d+", text)}
    claimed_numbers.update(
        number
        for word, number in _NUMBER_WORDS.items()
        if re.search(rf"\b{word}\b", text, re.IGNORECASE)
    )
    if not claimed_numbers.issubset(supported_numbers):
        raise AgentResponseValidationError(
            "The briefing contains a numeric claim not supported by the source records."
        )

    return {
        "overview": generated["overview"].strip(),
        "potential_impacts": generated["potential_impacts"].strip(),
    }


def validate_agent_response(
    tool_result: dict[str, Any],
    generated: Any,
    borough: Borough,
) -> dict[str, Any]:
    """Validate source records and generated claims before returning a briefing."""
    try:
        briefing = BriefingSuccessResponse.model_validate(tool_result)
    except ValidationError as error:
        raise AgentResponseValidationError(
            "The incident tool returned an invalid success response."
        ) from error

    if briefing.borough != borough:
        raise AgentResponseValidationError(
            "The incident tool returned records for a different borough."
        )
    if briefing.data_source != DataSource.NYC_OPEN_DATA:
        raise AgentResponseValidationError(
            "The incident tool returned an unexpected data source."
        )

    _validate_source_attribution(briefing)
    if not isinstance(generated, dict):
        raise AgentResponseValidationError("The model returned an invalid briefing.")
    generated_fields = _validate_generated_claims(generated, briefing, borough)
    return briefing.model_copy(update=generated_fields).model_dump(mode="json")