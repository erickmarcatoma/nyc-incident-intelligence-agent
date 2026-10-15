import { useState } from "react";

import AgentInput from "./components/AgentInput.jsx";
import BriefingResult from "./components/BriefingResult.jsx";

const BOROUGHS = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"];

export default function App() {
  const [borough, setBorough] = useState("Queens");
  const [question, setQuestion] = useState(
    "Summarize the most recent collision reports in Queens.",
  );
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [requestError, setRequestError] = useState("");

  async function submitBriefing(event) {
    event.preventDefault();
    setLoading(true);
    setRequestError("");
    setResult(null);

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
    } catch (error) {
      setRequestError(
        error instanceof Error
          ? error.message
          : "Could not connect to the briefing service. Check that both servers are running.",
      );
    } finally {
      setLoading(false);
    }
  }

  function chooseExample(prompt) {
    setQuestion(prompt);
    setResult(null);
    setRequestError("");
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="NYC Incident Intelligence home">
          <span className="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 32 32" fill="none">
              <path d="M16 3.5 27 9.8v12.4L16 28.5 5 22.2V9.8L16 3.5Z" />
              <path d="M10 19.5h12M12 15.5h8M14 11.5h4" />
            </svg>
          </span>
          <span className="brand-name">
            NYC <span>Incident Intelligence</span>
          </span>
        </a>
        <div className="topbar-note">SOURCE: NYC OPEN DATA</div>
      </header>

      <main>
        <section className="hero" aria-labelledby="page-title">
          <div className="hero-copy">
            <p className="eyebrow">
              <span className="eyebrow-rule" />
              City data, made clearer
            </p>
            <h1 id="page-title">
              A clearer view
              <br />
              of <span>NYC collisions.</span>
            </h1>
            <p className="hero-description">
              Ask a question about reported motor vehicle collisions and get a
              borough-specific briefing grounded in NYC Open Data.
            </p>
          </div>
          <div className="hero-aside" aria-label="Data source information">
            <span className="aside-label">DATASET</span>
            <strong>Motor Vehicle Collisions</strong>
            <span>NYC Open Data · Updated periodically</span>
            <a
              href="https://data.cityofnewyork.us/d/h9gi-nx95"
              target="_blank"
              rel="noreferrer"
            >
              Explore source <span aria-hidden="true">↗</span>
            </a>
          </div>
        </section>

        <section className="workspace" aria-label="Create an incident briefing">
          <div className="workspace-heading">
            <div>
              <span className="step-label">YOUR BRIEFING</span>
              <h2>What would you like to know?</h2>
            </div>
            <span className="response-time">
              <span aria-hidden="true">✳</span> AI-powered analysis
            </span>
          </div>

          <AgentInput
            borough={borough}
            boroughs={BOROUGHS}
            question={question}
            loading={loading}
            onBoroughChange={(value) => {
              setBorough(value);
              setQuestion(`Summarize the most recent collision reports in ${value}.`);
              setResult(null);
              setRequestError("");
            }}
            onQuestionChange={setQuestion}
            onSubmit={submitBriefing}
          />

          {requestError && (
            <div className="request-error" role="alert">
              <span aria-hidden="true">!</span>
              <div>
                <strong>Couldn’t get a briefing</strong>
                <p>{requestError}</p>
                <span>Make sure the backend is running at 127.0.0.1:8000.</span>
              </div>
            </div>
          )}

          {loading && (
            <div className="loading-card" role="status" aria-live="polite">
              <span className="loading-spinner" />
              <div>
                <strong>Putting your briefing together</strong>
                <p>Fetching NYC Open Data and preparing a grounded summary…</p>
              </div>
            </div>
          )}

          {result && <BriefingResult result={result} />}
        </section>

        <aside className="data-note">
          <span className="note-icon" aria-hidden="true">i</span>
          <p>
            <strong>About this data</strong>
            <span>
              These are reported crash records, not live traffic updates. NYC
              Open Data publication can lag the event date; a record does not
              indicate current road conditions.
            </span>
          </p>
        </aside>
      </main>

      <footer className="footer">
        <span>Built for a more informed New York.</span>
        <span>Source-grounded · Borough-specific · Not real-time</span>
      </footer>
    </div>
  );
}