from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.schemas import BriefingRequest, BriefingResponse
from backend.tools import query_511ny_incidents

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
def create_briefing(request: BriefingRequest) -> dict[str, Any]:
    return query_511ny_incidents(request.borough)