import { useState } from "react";

import AgentInput from "./components/AgentInput.jsx";
import BoroughSelector from "./components/BoroughSelector.jsx";
import BriefingResult, { BriefingShell } from "./components/BriefingResult.jsx";
import IncidentMap from "./components/IncidentMap.jsx";
import { BOROUGHS } from "./incidentUtils.js";

const defaultQuestion = (borough) => `What collisions were recently reported in ${borough}?`;

const EXAMPLES = [
  "Which recent crashes reported injuries?",
  "Summarize the latest collision reports.",
  "What patterns appear in these records?",
];

const NAV = [
  { label: "Home", href: "#top", icon: "M4 11.5 12 5l8 6.5V20h-5.5v-5h-5v5H4v-8.5Z" },
  { label: "Incidents", href: "#incidents", icon: "M12 4 21 19H3L12 4Zm0 6v4m0 2.5v.5" },
  { label: "Map", href: "#map", icon: "m4 6 5-2 6 2 5-2v14l-5 2-6-2-5 2V6Zm5-2v14m6-12v14" },
  { label: "About the data", href: "#about-data", icon: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Zm0-11v6m0-9v.5" },
];

export default function App() {
  const [borough, setBorough] = useState("Queens");
  const [question, setQuestion] = useState(defaultQuestion("Queens"));
  const [result, setResult] = useState(null);
  const [updatedAt, setUpdatedAt] = useState("");
  const [loading, setLoading] = useState(false);
  const [requestError, setRequestError] = useState("");

  async function submitBriefing(event) {
    event?.preventDefault();
    setLoading(true);
    setRequestError("");

    try {
      const response = await fetch("/api/briefing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ borough, question }),
      });
      const body = await response.json().catch(() => null);

      if (!response.ok) {
        const detail = body?.detail;
        const message = Array.isArray(detail)
          ? detail.map((item) => item.msg).join(" ")
          : typeof detail === "string"
            ? detail
            : `The server returned HTTP ${response.status}.`;
        throw new Error(message);
      }

      setResult(body);
      setUpdatedAt(
        new Intl.DateTimeFormat("en-US", { timeStyle: "short", timeZone: "America/New_York" }).format(
          new Date(),
        ),
      );
    } catch (error) {
      setResult(null);
      setRequestError(
        error instanceof Error
          ? error.message
          : "Could not connect to the briefing service. Check that both servers are running.",
      );
    } finally {
      setLoading(false);
    }
  }

  function changeBorough(value) {
    setBorough(value);
    setQuestion(defaultQuestion(value));
    setResult(null);
    setRequestError("");
  }

  const incidents = result?.status === "success" ? result.incidents : [];

  return (
    <div className="app-frame" id="top">
      <header className="app-header">
        <a className="brand" href="#top" aria-label="NYC Incident Intelligence Agent home">
          <span className="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 32 32">
              <path d="M16 3.5 27 9.8v12.4L16 28.5 5 22.2V9.8L16 3.5Z" />
              <path d="M10 19.5h12M12 15.5h8M14 11.5h4" />
            </svg>
          </span>
          <span>
            <strong>NYC Incident Intelligence Agent</strong>
            <span className="brand-tagline">Collision insights from NYC Open Data.</span>
          </span>
        </a>
        <BoroughSelector boroughs={BOROUGHS} value={borough} onChange={changeBorough} />
      </header>

      <div className="app-body">
        <aside className="sidebar">
          <nav aria-label="Sections">
            {NAV.map((item, index) => (
              <a key={item.label} href={item.href} className={`nav-item${index === 0 ? " is-active" : ""}`}>
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d={item.icon} />
                </svg>
                {item.label}
              </a>
            ))}
          </nav>
          <div className="sidebar-footer">
            <strong>Data source</strong>
            <a href="https://data.cityofnewyork.us/d/h9gi-nx95" target="_blank" rel="noreferrer">
              NYC Open Data · Motor Vehicle Collisions
            </a>
            <span>Independent project · not an official City service</span>
          </div>
        </aside>

        <main className="main">
          <AgentInput
            borough={borough}
            question={question}
            loading={loading}
            onQuestionChange={setQuestion}
            onSubmit={submitBriefing}
          />

          <div className="content-grid">
            <div className="briefing-column">
              {requestError && (
                <div className="request-error" role="alert">
                  <span aria-hidden="true">!</span>
                  <div>
                    <strong>Couldn’t get a briefing</strong>
                    <p>{requestError}</p>
                    <small>Make sure the backend is running at 127.0.0.1:8000.</small>
                  </div>
                </div>
              )}

              {loading && !result && (
                <BriefingShell>
                  <div className="briefing-state" role="status">
                    <span className="loading-spinner" />
                    <div>
                      <strong>Putting your briefing together</strong>
                      <p>Fetching NYC Open Data and preparing a grounded summary…</p>
                    </div>
                  </div>
                </BriefingShell>
              )}

              {result && (
                <div className={loading ? "is-refreshing" : undefined}>
                  <BriefingResult result={result} updatedAt={updatedAt} />
                </div>
              )}

              {!result && !loading && (
                <BriefingShell>
                  <div className="briefing-empty">
                    <strong>Ask about collisions in {borough}</strong>
                    <p>
                      You’ll get an overview, the source records, potential impacts and how fresh the
                      data is. Records are reported crashes, not live traffic.
                    </p>
                    <div className="example-prompts">
                      {EXAMPLES.map((example) => (
                        <button
                          type="button"
                          key={example}
                          onClick={() => setQuestion(`${example.replace(/[.?]$/, "")} in ${borough}?`)}
                        >
                          {example}
                        </button>
                      ))}
                    </div>
                  </div>
                </BriefingShell>
              )}
            </div>

            <IncidentMap borough={borough} incidents={incidents} />
          </div>
        </main>
      </div>
    </div>
  );
}
