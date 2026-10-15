import logging
import os
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.agent import AgentProtocolError, AgentUnavailableError, run_agent
from backend.schemas import (
    BriefingFailureResponse,
    BriefingRequest,
    BriefingResponse,
    DataSource,
)
from backend.tools import IncidentDataUnavailableError


logger = logging.getLogger(__name__)
DEFAULT_FRONTEND_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


def _frontend_origins() -> list[str]:
    configured_origins = os.getenv("FRONTEND_ORIGINS")
    if configured_origins is None:
        return list(DEFAULT_FRONTEND_ORIGINS)
    return [
        origin.strip()
        for origin in configured_origins.split(",")
        if origin.strip()
    ]

app = FastAPI(
    title="NYC Incident Intelligence Agent API",
    description=(
        "Anthropic-powered briefings over NYC Open Data Motor Vehicle Collisions "
        "records. This historical dataset is not a real-time traffic feed."
    ),
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_frontend_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/healthz")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/briefing", response_model=BriefingResponse)
def create_briefing(request: BriefingRequest) -> dict[str, Any]:
    try:
        return run_agent(request.borough)
    except IncidentDataUnavailableError:
        logger.exception("Could not retrieve NYC Open Data collision records.")
        return BriefingFailureResponse(
            status="data_unavailable",
            borough=request.borough,
            data_source=DataSource.NYC_OPEN_DATA,
            message=(
                "NYC Open Data is currently unavailable or returned unusable data. "
                "No briefing was generated."
            ),
        ).model_dump(mode="json")
    except (AgentProtocolError, AgentUnavailableError):
        logger.exception("Could not generate the requested incident briefing.")
        return BriefingFailureResponse(
            status="model_unavailable",
            borough=request.borough,
            data_source=None,
            message=(
                "The briefing model is currently unavailable. "
                "Please try again later."
            ),
        ).model_dump(mode="json")