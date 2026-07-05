import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'

const RISK_COLORS = {
  High: '#e63946',
  Medium: '#f4a261',
  Low: '#2a9d8f',
}

export default function HeatmapView({ points }) {
  const center = points.length
    ? [points[0].lat, points[0].lon]
    : [12.9716, 77.5946] // default demo center

  return (
    <MapContainer center={center} zoom={13} style={{ height: '360px', width: '100%' }}>
      <TileLayer
        attribution='&copy; OpenStreetMap contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {points.map((p, idx) => (
        <CircleMarker
          key={idx}
          center={[p.lat, p.lon]}
          radius={6 + Math.min(p.count, 10)}
          pathOptions={{
            color: RISK_COLORS[p.risk_level] || '#457b9d',
            fillColor: RISK_COLORS[p.risk_level] || '#457b9d',
            fillOpacity: 0.6,
          }}
        >
          <Popup>
            <strong>{p.risk_level} risk zone</strong><br />
            {p.count} detection(s) logged here
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  )
}
