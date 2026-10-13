import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.schemas import (
    BriefingRequest,
    BriefingResponse,
    BriefingSuccessResponse,
    DataSource,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "queens_success.json"
FIXTURE_RESPONSE = BriefingSuccessResponse.model_validate(
    json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
)

app = FastAPI(
    title="NYC Incident Intelligence Agent API",
    description="Day 1 fixture-backed API; no live incident source is queried.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.post("/api/briefing", response_model=BriefingResponse)
def create_briefing(request: BriefingRequest) -> BriefingSuccessResponse:
    incident = FIXTURE_RESPONSE.incidents[0].model_copy(
        update={
            "location": (
                f"Fictional fixture location in {request.borough.value} "
                "(not a real incident)"
            )
        }
    )
    return FIXTURE_RESPONSE.model_copy(
        update={
            "borough": request.borough,
            "data_source": DataSource.FIXTURE,
            "incidents": [incident],
        }
    )