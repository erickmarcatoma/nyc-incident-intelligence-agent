function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "America/New_York",
  }).format(date);
}

export default function IncidentCard({ incident }) {
  return (
    <article className="incident-card">
      <div className="incident-card-top">
        <span className="incident-type">
          <span className="incident-marker" />
          {incident.type}
        </span>
        <span className="incident-id">#{incident.id}</span>
      </div>
      <h4>{incident.location}</h4>
      <p className="incident-status">{incident.reported_status}</p>
      <div className="incident-card-bottom">
        <time dateTime={incident.reported_at}>{formatDate(incident.reported_at)}</time>
        {incident.source_url ? (
          <a href={incident.source_url} target="_blank" rel="noreferrer">
            Source record <span aria-hidden="true">↗</span>
          </a>
        ) : (
          <span>{incident.source}</span>
        )}
      </div>
    </article>
  );
}