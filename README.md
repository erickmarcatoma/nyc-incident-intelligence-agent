# NYC Incident Intelligence Agent

A fixture-backed prototype for requesting source-grounded traffic incident briefings by NYC borough. The Day 1 API returns fictional fixture data only; it does not query 511NY and must not be used for operational decisions.

## Backend setup

Requires Python 3.12 or later.

From the repository root in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python -m uvicorn backend.main:app --reload
```

The API runs at `http://127.0.0.1:8000`; interactive API documentation is at `http://127.0.0.1:8000/docs`.

## Day 1 contract

`POST /api/briefing` accepts a borough (`Manhattan`, `Brooklyn`, `Queens`, `Bronx`, or `Staten Island`) and a nonblank question of up to 500 characters. It returns a `success` response with a fixture label, incident details, freshness, and limitations. `reported_at` timestamps include an ISO 8601 timezone offset; `source_url` is optional and may be `null`.

Example request:

```json
{
  "borough": "Queens",
  "question": "What traffic incidents are affecting Queens?"
}
```

The development API allows browser requests from the Vite origins `http://localhost:5173` and `http://127.0.0.1:5173`.

Run backend tests from the repository root:

```powershell
python -m pytest backend\tests
```

## Secrets

Copy `.env.example` to `.env` only when configuring the later Claude integration. Keep `.env` out of version control. The Day 1 fixture API does not need an API key.

511NY access and field mappings remain unverified; see [backend/SOURCE_NOTES.md](./backend/SOURCE_NOTES.md).
