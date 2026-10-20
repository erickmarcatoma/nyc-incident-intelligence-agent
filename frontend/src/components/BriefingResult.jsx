import IncidentCard from "./IncidentCard.jsx";
import { toBullets } from "../incidentUtils.js";

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

function Section({ number, title, children, id }) {
  return (
    <section className="brief-section" id={id}>
      <h3 className="brief-heading">
        <span className="brief-number">{number}</span>
        {title}
        <span className="brief-rule" aria-hidden="true" />
      </h3>
      <div className="brief-body">{children}</div>
    </section>
  );
}

export function BriefingShell({ updatedAt, children }) {
  return (
    <article className="briefing-card" aria-live="polite">
      <header className="briefing-card-header">
        <span className="briefing-title">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 2.5c.6 4.6 2.9 6.9 7.5 7.5-4.6.6-6.9 2.9-7.5 7.5-.6-4.6-2.9-6.9-7.5-7.5 4.6-.6 6.9-2.9 7.5-7.5Z" />
          </svg>
          AI INTELLIGENCE BRIEFING
        </span>
        {updatedAt && <span className="briefing-updated">Updated {updatedAt}</span>}
      </header>
      {children}
    </article>
  );
}

export default function BriefingResult({ result, updatedAt }) {
  if (result.status !== "success") {
    const copy = FAILURE_COPY[result.status] ?? {
      title: "A briefing could not be generated",
      detail: result.message ?? "The service returned an unrecognized response.",
    };
    return (
      <BriefingShell updatedAt={updatedAt}>
        <div className="briefing-state is-failure">
          <span className="state-icon" aria-hidden="true">!</span>
          <div>
            <strong>{copy.title}</strong>
            <p>{result.message || copy.detail}</p>
          </div>
        </div>
      </BriefingShell>
    );
  }

  const impacts = toBullets(result.potential_impacts);

  return (
    <BriefingShell updatedAt={updatedAt}>
      <Section number={1} title="INCIDENT OVERVIEW">
        <p className="overview-text">{result.overview}</p>
      </Section>

      <Section number={2} title="REPORTED INCIDENTS" id="incidents">
        <div className="incident-list">
          {result.incidents.map((incident) => (
            <IncidentCard key={incident.id} incident={incident} />
          ))}
        </div>
      </Section>

      <Section number={3} title="POTENTIAL IMPACTS">
        {impacts.length > 1 ? (
          <ul className="impact-list">
            {impacts.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : (
          <p className="overview-text">{result.potential_impacts}</p>
        )}
      </Section>

      <Section number={4} title="DATA FRESHNESS & LIMITATIONS" id="about-data">
        <div className="freshness-box">
          <span className="info-icon" aria-hidden="true">i</span>
          <div>
            <p>{result.data_freshness}</p>
            <p className="freshness-note">{result.limitations}</p>
          </div>
        </div>
      </Section>
    </BriefingShell>
  );
}
