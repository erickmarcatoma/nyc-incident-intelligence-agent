from datetime import datetime
from enum import Enum
from typing import Annotated, Literal, TypeAlias

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator


class Borough(str, Enum):
    MANHATTAN = "Manhattan"
    BROOKLYN = "Brooklyn"
    QUEENS = "Queens"
    BRONX = "Bronx"
    STATEN_ISLAND = "Staten Island"


class DataSource(str, Enum):
    FIXTURE = "fixture"
    LIVE = "live"


class BriefingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    borough: Borough
    question: str = Field(min_length=1, max_length=500)

    @field_validator("question")
    @classmethod
    def trim_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question must not be blank")
        return value


class Incident(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    location: str = Field(min_length=1)
    type: str = Field(min_length=1)
    reported_status: str = Field(min_length=1)
    reported_at: datetime
    source: str = Field(min_length=1)
    source_url: AnyHttpUrl | None = None

    @field_validator("reported_at")
    @classmethod
    def require_timezone_offset(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("reported_at must include a timezone offset")
        return value


class BriefingSuccessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["success"] = "success"
    borough: Borough
    data_source: DataSource
    overview: str = Field(min_length=1)
    incidents: list[Incident] = Field(min_length=1)
    potential_impacts: str = Field(min_length=1)
    data_freshness: str = Field(min_length=1)
    limitations: str = Field(min_length=1)


class BriefingFailureResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["no_results", "data_unavailable", "model_unavailable"]
    borough: Borough
    data_source: DataSource | None = None
    message: str = Field(min_length=1)


BriefingResponse: TypeAlias = Annotated[
    BriefingSuccessResponse | BriefingFailureResponse,
    Field(discriminator="status"),
]