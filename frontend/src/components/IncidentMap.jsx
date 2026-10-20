import { useEffect, useRef } from "react";

import { BOROUGH_VIEWS, SEVERITY, coordinatesOf, severityOf } from "../incidentUtils.js";

// Leaflet is loaded from a CDN in index.html, so it lives on window.L.
function leaflet() {
  return typeof window !== "undefined" ? window.L : undefined;
}

function pinIcon(L, color) {
  return L.divIcon({
    className: "map-pin",
    html: `<span style="--pin:${color}"></span>`,
    iconSize: [26, 34],
    iconAnchor: [13, 32],
    popupAnchor: [0, -28],
  });
}

function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
}

export default function IncidentMap({ borough, incidents }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const layerRef = useRef(null);

  useEffect(() => {
    const L = leaflet();
    if (!L || !containerRef.current || mapRef.current) return undefined;
    const view = BOROUGH_VIEWS[borough];
    const map = L.map(containerRef.current, {
      zoomControl: false,
      attributionControl: true,
    }).setView(view.center, view.zoom);
    L.control.zoom({ position: "bottomright" }).addTo(map);
    L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
      maxZoom: 19,
      subdomains: "abcd",
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    }).addTo(map);
    layerRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
    // The map is created once; later effects move it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const L = leaflet();
    const map = mapRef.current;
    if (!L || !map) return;
    layerRef.current.clearLayers();

    const points = [];
    for (const incident of incidents) {
      const coords = coordinatesOf(incident);
      if (!coords) continue;
      const severity = severityOf(incident);
      points.push(coords);
      L.marker(coords, { icon: pinIcon(L, SEVERITY[severity.key].color), title: incident.location })
        .bindPopup(
          `<strong>${escapeHtml(incident.type)}</strong><br>${escapeHtml(incident.reported_status)}`,
        )
        .addTo(layerRef.current);
    }

    if (points.length > 1) {
      map.fitBounds(points, { padding: [48, 48], maxZoom: 14 });
    } else if (points.length === 1) {
      map.setView(points[0], 14);
    } else {
      const view = BOROUGH_VIEWS[borough];
      map.setView(view.center, view.zoom);
    }
  }, [borough, incidents]);

  const mapped = incidents.filter((incident) => coordinatesOf(incident)).length;
  const hasLeaflet = Boolean(leaflet());

  return (
    <section className="map-card" id="map" aria-label={`Map of ${borough}`}>
      <div ref={containerRef} className="map-canvas" />
      {!hasLeaflet && <div className="map-fallback">The map library could not load.</div>}

      <span className="map-borough-label">{borough.toUpperCase()}</span>

      <ul className="map-legend" aria-label="Map legend">
        {["fatal", "injury", "none"].map((key) => (
          <li key={key}>
            <span style={{ background: SEVERITY[key].color }} />
            {SEVERITY[key].label}
          </li>
        ))}
      </ul>

      {incidents.length > 0 && mapped < incidents.length && (
        <p className="map-note">
          {mapped} of {incidents.length} records include coordinates and are shown on the map.
        </p>
      )}
    </section>
  );
}
