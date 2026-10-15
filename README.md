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

## Optional local Docker backend

To run the backend in a local Docker container, build the image from the
repository root:

```powershell
docker build -t nyc-incident-intelligence-backend .
docker run --rm --env-file .env -p 8000:8000 nyc-incident-intelligence-backend
```

The container runs as a non-root user and listens on port `8000` by default
(`PORT` can override the container port). Configure `ANTHROPIC_API_KEY` in the
runtime `.env` file; secrets are excluded from the build context and are not
copied into the image. Set `FRONTEND_ORIGINS` to a comma-separated list of
trusted frontend origins if needed; the default allows the two local Vite
origins only. `GET /healthz` is the container health check. No hosted deployment
is configured or required for this project.

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

Before Claude summarizes the records, the backend deterministically groups
street-name locations (case- and order-normalized) and sums reported injuries.
An intersection is included in the high-injury summary when its known reported
injuries total at least 3. Coordinates-only locations are not grouped, and
unreported injury counts are not treated as zero. Claude receives these
precomputed metrics for narrative synthesis; it is not asked to calculate them.

## System prompt v1 security and scope

The active prompt is `SYSTEM_PROMPT` in `backend/agent.py`; no separate PRD file
is present in this repository. It treats retrieved records as untrusted,
prohibits disclosing or referencing backend secrets, disallows raw HTML and
executable code, and restricts the agent to read-only situational awareness.
When asked to dispatch services or change records, the agent must explain that
it cannot perform those actions.

The API keeps its JSON response contract (`overview` and `potential_impacts`).
Claude is instructed to use standard Markdown only within those text fields;
the backend independently rejects outputs containing sensitive configuration
references, raw HTML, executable code patterns, or claims of official actions.

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

## Local demo checklist

1. Configure a valid `ANTHROPIC_API_KEY` in the repository-root `.env` file.
   `NYC_OPEN_DATA_APP_TOKEN` is optional.
2. Start the backend and frontend using the instructions above.
3. Confirm the backend is healthy at `http://127.0.0.1:8000/healthz`, then open
   `http://127.0.0.1:5173`.
4. Select a borough and ask for recent collision reports. Check the borough,
   record links, New York timestamps, freshness, and limitations in the result.
5. Rehearse one failure state: stop the backend to show the connection error,
   or temporarily use an invalid Anthropic key to show `model_unavailable`.
   Restore the valid key before normal use.

If no Anthropic key is configured, the NYC Open Data tool can still be tested
directly, but a full briefing request will return `model_unavailable`; the app
does not substitute fixture data. Automated backend evals mock Claude and source
responses so they run without credentials. Run them with
`python -m pytest backend\tests`.

The app uses NYC Open Data's Motor Vehicle Collisions - Crashes dataset, not
511NY. The source contains historical collision reports, may lag by months, and
does not provide current traffic or road-closure status. See
[backend/SOURCE_NOTES.md](./backend/SOURCE_NOTES.md) for verified source details
and limitations.
