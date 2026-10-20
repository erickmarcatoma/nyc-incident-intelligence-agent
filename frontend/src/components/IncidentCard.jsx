import { SEVERITY, formatTime, severityBadge, severityOf } from "../incidentUtils.js";

function SeverityIcon({ severityKey }) {
  const color = SEVERITY[severityKey].color;
  return (
    <span className="incident-icon" style={{ "--sev": color }} aria-hidden="true">
      <svg viewBox="0 0 24 24">
        <path d="M6 15.5h12M7 15.5l1.4-5a1.5 1.5 0 0 1 1.4-1h4.4a1.5 1.5 0 0 1 1.4 1l1.4 5v2.5H7v-2.5Z" />
        <circle cx="9" cy="18.5" r="1.2" />
        <circle cx="15" cy="18.5" r="1.2" />
      </svg>
    </span>
  );
}

export default function IncidentCard({ incident }) {
  const severity = severityOf(incident);
  const { time, day } = formatTime(incident.reported_at);
  const sourceName = incident.source?.startsWith("NYC Open Data") ? "NYC Open Data" : incident.source;

  return (
    <article className="incident-row">
      <SeverityIcon severityKey={severity.key} />
      <div className="incident-main">
        <h4>{incident.location}</h4>
        <p>
          {incident.type} · {incident.reported_status}
        </p>
      </div>
      <span className={`severity-badge sev-${severity.key}`}>{severityBadge(severity)}</span>
      <time className="incident-time" dateTime={incident.reported_at}>
        <strong>{time}</strong>
        <span>{day}</span>
      </time>
      {incident.source_url ? (
        <a className="incident-source" href={incident.source_url} target="_blank" rel="noreferrer">
          {sourceName}
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" />
          </svg>
        </a>
      ) : (
        <span className="incident-source">{sourceName}</span>
      )}
    </article>
  );
}
