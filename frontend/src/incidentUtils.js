export const BOROUGHS = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"];

export const BOROUGH_VIEWS = {
  Manhattan: { center: [40.7831, -73.9712], zoom: 12 },
  Brooklyn: { center: [40.6501, -73.9496], zoom: 11 },
  Queens: { center: [40.7282, -73.7949], zoom: 11 },
  Bronx: { center: [40.8448, -73.8648], zoom: 12 },
  "Staten Island": { center: [40.5795, -74.1502], zoom: 11 },
};

export const SEVERITY = {
  fatal: { label: "Fatality reported", short: "FATAL", color: "#d93a3a" },
  injury: { label: "Injuries reported", short: "INJURY", color: "#e3a325" },
  none: { label: "No injuries reported", short: "NO INJURY", color: "#2f6fd1" },
  unknown: { label: "Other record", short: "REPORTED", color: "#7a8699" },
};

function countAfter(text, word) {
  const match = text.match(new RegExp(`${word}:\\s*(\\d+)`, "i"));
  return match ? Number(match[1]) : null;
}

/** Reads "Reported persons injured: N; persons killed: M." from the backend. */
export function severityOf(incident) {
  const status = incident.reported_status ?? "";
  const injured = countAfter(status, "injured");
  const killed = countAfter(status, "killed");
  if (killed === null && injured === null) return { key: "unknown", injured, killed };
  if (killed > 0) return { key: "fatal", injured, killed };
  if (injured > 0) return { key: "injury", injured, killed };
  return { key: "none", injured, killed };
}

export function severityBadge({ key, injured, killed }) {
  if (key === "fatal") return `${killed} KILLED`;
  if (key === "injury") return `${injured} INJURED`;
  return SEVERITY[key].short;
}

/** The backend only exposes coordinates as "Near latitude X, longitude Y". */
export function coordinatesOf(incident) {
  const match = (incident.location ?? "").match(
    /latitude\s+(-?\d+(?:\.\d+)?),\s*longitude\s+(-?\d+(?:\.\d+)?)/i,
  );
  if (!match) return null;
  const lat = Number(match[1]);
  const lng = Number(match[2]);
  if (!lat || !lng) return null;
  return [lat, lng];
}

export function formatTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return { time: value, day: "" };
  const zone = { timeZone: "America/New_York" };
  return {
    time: new Intl.DateTimeFormat("en-US", { ...zone, timeStyle: "short" }).format(date),
    day: new Intl.DateTimeFormat("en-US", { ...zone, dateStyle: "medium" }).format(date),
  };
}

/** Turns the backend's prose into bullets when it has several sentences or lines. */
export function toBullets(text) {
  if (!text) return [];
  const lines = text
    .split(/\n+/)
    .map((line) => line.replace(/^\s*[-•*]\s*/, "").trim())
    .filter(Boolean);
  if (lines.length > 1) return lines;
  return text
    .split(/(?<=[.!?])\s+(?=[A-Z])/)
    .map((sentence) => sentence.trim())
    .filter(Boolean);
}
