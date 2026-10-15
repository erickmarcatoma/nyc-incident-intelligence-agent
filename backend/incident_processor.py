import re
from typing import Any, Iterable
from urllib.parse import parse_qs, urlparse

from pydantic import ValidationError

from backend.schemas import Borough, BriefingSuccessResponse, DataSource, Incident


DATASET_HOST = "data.cityofnewyork.us"
DATASET_PATH = "/resource/h9gi-nx95.json"
DATASET_SOURCE = "NYC Open Data: Motor Vehicle Collisions - Crashes"
HIGH_INJURY_THRESHOLD = 3
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
_REPORTED_TOTAL_CLAIM = re.compile(
    rf"\b({_NUMBER_TOKEN})\s+(?:(?:motor vehicle\s+)?"
    r"(?:collisions?|crashes?|incidents?|records?))\s+"
    r"(?:were|was)\s+(?:reported|returned|retrieved|recorded)\b",
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
_HIGH_INJURY_INTERSECTION_COUNT = re.compile(
    rf"\b({_NUMBER_TOKEN})\s+high[- ]injury intersections?\b",
    re.IGNORECASE,
)
_INTERSECTION_COUNT = re.compile(
    rf"\b({_NUMBER_TOKEN})\s+(?:(?:distinct|unique|known)\s+)?intersections?\b",
    re.IGNORECASE,
)
_CURRENT_CONDITION_CLAIM = re.compile(
    r"\b(?:currently\s+(?:active|ongoing|closed|open|clear|congested|"
    r"affecting|blocking|causing)|(?:is|remains|stays)\s+"
    r"(?:active|ongoing|closed|open|clear|congested|affecting|blocking|causing)|"
    r"still\s+(?:active|ongoing|closed|open|clear|congested|affecting|blocking))\b",
    re.IGNORECASE,
)
_SENSITIVE_REFERENCE = re.compile(
    r"\b(?:api[\s_-]?keys?|credentials?|environment variables?|secrets?)\b"
    r"|\b(?:access|auth|bearer)\s+tokens?\b"
    r"|\bANTHROPIC_[A-Z0-9_]+\b"
    r"|\bNYC_OPEN_DATA_APP_TOKEN\b"
    r"|\bsk-ant-[A-Za-z0-9_-]{8,}\b",
    re.IGNORECASE,
)
_RAW_HTML = re.compile(r"</?[A-Za-z][^>]*>")
_EXECUTABLE_TEXT = re.compile(
    r"```|javascript:|\bfunction\s+\w+\s*\(|\b(?:const|let|var)\s+"
    r"[A-Za-z_$][\w$]*\s*=|\b(?:document|window)\."
    r"|\b(?:eval|alert|fetch|setTimeout|setInterval)\s*\("
    r"|\bconsole\.\w+\s*\(",
    re.IGNORECASE,
)
_CLAIMED_OPERATION = re.compile(
    r"\b(?:I|we)\s+(?:(?:have\s+)?"
    r"(?:dispatched|sent|contacted|modified|updated|changed|submitted|"
    r"approved|ordered|authorized)|(?:can|will|am able to)\s+"
    r"(?:dispatch|send|contact|modify|update|change|submit|approve|order|"
    r"authorize|make official decisions))\b"
    r"|\b(?:emergency services|government records|municipal records)\s+"
    r"(?:have been|were|are being)\s+"
    r"(?:dispatched|sent|modified|updated|changed|submitted|approved)\b",
    re.IGNORECASE,
)


class AgentResponseValidationError(ValueError):
    """The generated briefing is invalid or unsupported by its source records."""


def _injury_count(incident: Incident) -> int | None:
    match = re.search(
        r"Reported persons injured: (\d+|not reported);",
        incident.reported_status,
    )
    if match is None or match.group(1) == "not reported":
        return None
    return int(match.group(1))


def _intersection_streets(location: str) -> tuple[str, ...]:
    if location.casefold().startswith("near latitude "):
        return ()
    streets = {
        re.sub(r"[^A-Z0-9]+", " ", street.upper()).strip()
        for street in location.split(",")
    }
    streets.discard("")
    return tuple(sorted(street for street in streets if street))


def analyze_incidents(incidents: Iterable[Incident]) -> dict[str, Any]:
    """Calculate reproducible collision and injury metrics from normalized records."""
    groups: dict[tuple[str, ...], dict[str, Any]] = {}
    incident_count = 0
    for incident in incidents:
        incident_count += 1
        streets = _intersection_streets(incident.location)
        if len(streets) < 2:
            continue
        group = groups.setdefault(
            streets,
            {
                "intersection": " / ".join(streets),
                "collision_count": 0,
                "reported_injuries": 0,
                "injury_reports_complete": True,
            },
        )
        group["collision_count"] += 1
        injuries = _injury_count(incident)
        if injuries is None:
            group["injury_reports_complete"] = False
        else:
            group["reported_injuries"] += injuries

    intersections = sorted(
        groups.values(),
        key=lambda group: group["intersection"],
    )
    high_injury_intersections = [
        group
        for group in intersections
        if group["reported_injuries"] >= HIGH_INJURY_THRESHOLD
    ]
    unclassified_intersection_count = sum(
        not group["injury_reports_complete"]
        and group["reported_injuries"] < HIGH_INJURY_THRESHOLD
        for group in intersections
    )
    return {
        "incident_count": incident_count,
        "intersection_count": len(intersections),
        "high_injury_threshold": HIGH_INJURY_THRESHOLD,
        "high_injury_intersections": high_injury_intersections,
        "unclassified_intersection_count": unclassified_intersection_count,
    }


def _number_value(value: str) -> int:
    return int(value) if value.isdigit() else _NUMBER_WORDS[value.casefold()]


def _validate_count_claims(
    text: str,
    briefing: BriefingSuccessResponse,
    analysis: dict[str, Any],
) -> None:
    incident_count = len(briefing.incidents)
    for match in _REPORTED_TOTAL_CLAIM.finditer(text):
        if _number_value(match.group(1)) != incident_count:
            raise AgentResponseValidationError(
                "The briefing reports an unsupported number of total records."
            )
    for match in _INCIDENT_COUNT_CLAIM.finditer(text):
        count = _number_value(match.group(1))
        if count == 0 or count > incident_count:
            raise AgentResponseValidationError(
                "The briefing reports an unsupported number of incidents."
            )

    high_injury_count = len(analysis["high_injury_intersections"])
    for match in _HIGH_INJURY_INTERSECTION_COUNT.finditer(text):
        if _number_value(match.group(1)) != high_injury_count:
            raise AgentResponseValidationError(
                "The briefing reports an unsupported number of high-injury intersections."
            )
    for match in _INTERSECTION_COUNT.finditer(text):
        if _number_value(match.group(1)) != analysis["intersection_count"]:
            raise AgentResponseValidationError(
                "The briefing reports an unsupported number of intersections."
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
        supported_counts = set(known_counts)
        if len(known_counts) == incident_count:
            supported_counts.add(sum(known_counts))
        if count not in supported_counts:
            raise AgentResponseValidationError(
                "The briefing reports an unsupported injury or fatality count."
            )

    for match in _INJURY_COUNT_CLAIM.finditer(text):
        count = _number_value(match.group(1))
        known_counts = (
            injury_counts if match.group(2).casefold() == "injuries" else fatality_counts
        )
        supported_counts = set(known_counts)
        if len(known_counts) == incident_count:
            supported_counts.add(sum(known_counts))
        if count not in supported_counts:
            raise AgentResponseValidationError(
                "The briefing reports an unsupported injury or fatality count."
            )


def _supported_numbers(
    briefing: BriefingSuccessResponse,
    analysis: dict[str, Any],
) -> set[int]:
    supported = {len(briefing.incidents)}
    supported.update(
        (
            analysis["intersection_count"],
            analysis["high_injury_threshold"],
            len(analysis["high_injury_intersections"]),
            analysis["unclassified_intersection_count"],
        )
    )
    for intersection in analysis["high_injury_intersections"]:
        supported.update(
            (
                intersection["collision_count"],
                intersection["reported_injuries"],
            )
        )
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
    analysis: dict[str, Any],
) -> dict[str, str]:
    if set(generated) != {"overview", "potential_impacts"} or not all(
        isinstance(generated.get(field), str) and generated[field].strip()
        for field in ("overview", "potential_impacts")
    ):
        raise AgentResponseValidationError("The model returned an invalid briefing.")

    text = " ".join(generated[field] for field in ("overview", "potential_impacts"))
    if _SENSITIVE_REFERENCE.search(text):
        raise AgentResponseValidationError(
            "The briefing references sensitive backend configuration."
        )
    if _RAW_HTML.search(text):
        raise AgentResponseValidationError(
            "The briefing contains raw HTML, which is not allowed."
        )
    if _EXECUTABLE_TEXT.search(text):
        raise AgentResponseValidationError(
            "The briefing contains executable code, which is not allowed."
        )
    if _CLAIMED_OPERATION.search(text):
        raise AgentResponseValidationError(
            "The briefing claims an official action outside the agent's read-only scope."
        )
    if _CURRENT_CONDITION_CLAIM.search(text):
        raise AgentResponseValidationError(
            "The briefing makes an unsupported claim about current traffic conditions."
        )
    _validate_count_claims(text, briefing, analysis)

    mentioned_boroughs = {
        name.casefold()
        for name in (name.value for name in Borough)
        if re.search(rf"\b{re.escape(name)}\b", text, re.IGNORECASE)
    }
    if mentioned_boroughs - {borough.value.casefold()}:
        raise AgentResponseValidationError(
            "The briefing mentions a borough other than the selected borough."
        )

    supported_numbers = _supported_numbers(briefing, analysis)
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
    analysis = analyze_incidents(briefing.incidents)
    generated_fields = _validate_generated_claims(
        generated,
        briefing,
        borough,
        analysis,
    )
    return briefing.model_copy(update=generated_fields).model_dump(mode="json")