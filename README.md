# NYC Incident Intelligence Agent

An Anthropic-powered prototype for requesting NYC motor vehicle collision briefings by borough. Claude summarizes records fetched from NYC Open Data's Motor Vehicle Collisions - Crashes dataset (`h9gi-nx95`). These are real crash records, but publication can lag the event date; this is not a live traffic conditions feed. Do not use the briefings for emergency response or other operational decisions.

## Backend setup

Requires Python 3.12 or later.

From the repository root in PowerShell:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Set ANTHROPIC_API_KEY in .env. NYC_OPEN_DATA_APP_TOKEN is optional.
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python -m uvicorn backend.main:app --reload
```

The API runs at `http://127.0.0.1:8000`; interactive API documentation is at `http://127.0.0.1:8000/docs`.

## Run the frontend

Start the backend as described above. In a second PowerShell window, from the repository root:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. The Vite development server proxies `/api` requests to the backend at `http://127.0.0.1:8000`, so both servers need to be running. Select a borough, enter a question, and choose **Get briefing**. The page shows the AI summary, returned NYC Open Data records, record links, and freshness/limitations. Requests use your server-side `.env`; the API key is never sent to the browser.

## Briefing API

`POST /api/briefing` accepts a borough (`Manhattan`, `Brooklyn`, `Queens`, `Bronx`, or `Staten Island`) and a nonblank question of up to 500 characters. The backend asks Claude to call its read-only incident retrieval tool, executes that tool in Python, and uses Claude to summarize successful results. The API key remains server-side; configure it as `ANTHROPIC_API_KEY` in `.env`. `ANTHROPIC_MODEL` is optional and defaults to `claude-sonnet-4-5`.

The incident tool queries NYC Open Data's `h9gi-nx95` dataset, filters by borough, and returns up to 50 of the latest crash records. `NYC_OPEN_DATA_APP_TOKEN` is optional; anonymous API access is supported, while a Socrata app token may improve request limits. The API reports `data_source: "nyc_open_data"` and includes each record's dataset link and event timestamp. The source's publication can lag; the latest record returned may be months old. No fixture is used as a fallback.

`reported_at` is the dataset's local crash date and time, converted to the `America/New_York` time zone. A zero-row response returns `no_results` and does not mean there were no crashes in the borough. Source failures return `data_unavailable`; Anthropic failures return `model_unavailable`. The backend does not turn either failure into fixture data or an empty success.

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

Keep `.env` out of version control. A valid `ANTHROPIC_API_KEY` is required to generate summaries. The NYC Open Data endpoint can be queried without a token; if `NYC_OPEN_DATA_APP_TOKEN` is set, the backend sends it only to data.cityofnewyork.us.

The 511NY feed remains unverified and is not used. See [backend/SOURCE_NOTES.md](./backend/SOURCE_NOTES.md) for source details and limitations.
