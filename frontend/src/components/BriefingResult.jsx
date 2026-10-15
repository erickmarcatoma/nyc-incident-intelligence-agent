import IncidentCard from "./IncidentCard.jsx";

const FAILURE_COPY = {
  no_results: {
    title: "No matching records found",
    detail:
      "NYC Open Data returned no matching collision records for this borough. This does not mean there were no crashes.",
  },
  data_unavailable: {
    title: "Incident data is unavailable",
    detail: "The data source could not provide usable records. Please try again later.",
  },
  model_unavailable: {
    title: "The briefing service is unavailable",
    detail: "The model could not prepare a briefing. Please try again in a moment.",
  },
};

export default function BriefingResult({ result }) {
  if (result.status !== "success") {
    const copy = FAILURE_COPY[result.status] ?? {
      title: "A briefing could not be generated",
      detail: result.message ?? "The service returned an unrecognized response.",
    };

    return (
      <section className="result-panel failure-panel" aria-live="polite">
        <div className="result-section-heading">
          <span className="result-icon failure-icon" aria-hidden="true">!</span>
          <div>
            <span className="step-label">BRIEFING STATUS</span>
            <h3>{copy.title}</h3>
          </div>
        </div>
        <p>{result.message || copy.detail}</p>
      </section>
    );
  }

  return (
    <section className="result-panel" aria-live="polite">
      <div className="result-heading">
        <div className="result-section-heading">
          <span className="result-icon" aria-hidden="true">✓</span>
          <div>
            <span className="step-label">YOUR BRIEFING</span>
            <h3>{result.borough} collision briefing</h3>
          </div>
        </div>
        <span className="source-badge">
          <span className="status-dot" />
          {result.data_source === "nyc_open_data" ? "NYC Open Data" : result.data_source}
        </span>
      </div>

      <div className="briefing-copy">
        <div className="briefing-section">
          <span className="section-kicker">OVERVIEW</span>
          <p>{result.overview}</p>
        </div>
        <div className="briefing-section impacts-section">
          <span className="section-kicker">POTENTIAL IMPACTS</span>
          <p>{result.potential_impacts}</p>
        </div>
      </div>

      <div className="records-heading">
        <div>
          <span className="section-kicker">SOURCE RECORDS</span>
          <h3>{result.incidents.length} reported collisions</h3>
        </div>
        <span className="records-caption">Most recent first · New York time</span>
      </div>

      <div className="incident-list">
        {result.incidents.map((incident) => (
          <IncidentCard key={incident.id} incident={incident} />
        ))}
      </div>

      <div className="freshness-panel">
        <span className="freshness-icon" aria-hidden="true">◷</span>
        <div>
          <strong>Data freshness &amp; limitations</strong>
          <p>{result.data_freshness}</p>
          <p>{result.limitations}</p>
        </div>
      </div>
    </section>
  );
}