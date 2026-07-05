import { useEffect, useRef, useState } from 'react'
import HeatmapView from './components/HeatmapView.jsx'
import AlertPanel from './components/AlertPanel.jsx'
import AnalyticsCharts from './components/AnalyticsCharts.jsx'
import IncidentUploader from './components/IncidentUploader.jsx'
import LiveWebcam from './components/LiveWebcam.jsx'

// Fires a real OS-level desktop notification (falls back silently if
// the browser blocks/denies permission — the in-dashboard alert still shows).
function notifyDriver(animal, riskLevel, message) {
  if (!('Notification' in window)) return
  const fire = () => {
    new Notification(riskLevel === 'High' ? '🚨 REDUCE SPEED NOW' : '⚠️ Animal Ahead', {
      body: message,
      tag: 'wildlife-alert',
    })
  }
  if (Notification.permission === 'granted') {
    fire()
  } else if (Notification.permission !== 'denied') {
    Notification.requestPermission().then(p => { if (p === 'granted') fire() })
  }
}

const WS_URL = `ws://${window.location.hostname}:8000/ws`

export default function App() {
  const [alerts, setAlerts] = useState([])
  const [incidents, setIncidents] = useState([])
  const [heatmapPoints, setHeatmapPoints] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)

  const refreshData = () => {
    fetch('/api/incidents').then(r => r.json()).then(setIncidents).catch(() => {})
    fetch('/api/heatmap').then(r => r.json()).then(setHeatmapPoints).catch(() => {})
    fetch('/api/analytics').then(r => r.json()).then(setAnalytics).catch(() => {})
  }

  useEffect(() => {
    refreshData()
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }

    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setAlerts(prev => [data, ...prev].slice(0, 30))

      if (data.type === 'detection') {
        notifyDriver(data.incident.animal_type, data.incident.risk_level, data.alert)
        refreshData()
      }
      if (data.type === 'emergency') {
        notifyDriver(data.incident.animal_type, 'High', data.message)
        refreshData()
      }
    }
    return () => ws.close()
  }, [])

  return (
    <div className="app">
      <header className="app-header">
        <h1>🐾 Roadside Wildlife Collision Prevention</h1>
        <span className={`status-dot ${connected ? 'online' : 'offline'}`}>
          {connected ? 'Live' : 'Disconnected'}
        </span>
      </header>

      <div className="grid">
        <section className="card map-card">
          <h2>🗺️ Smart Risk Heatmap</h2>
          <HeatmapView points={heatmapPoints} />
        </section>

        <section className="card alert-card">
          <h2>⚠️ Live Alerts</h2>
          <AlertPanel alerts={alerts} />
        </section>

        <section className="card upload-card">
          <h2>🧠 Run Detection</h2>
          <LiveWebcam onProcessed={refreshData} />
          <hr className="divider" />
          <IncidentUploader onProcessed={refreshData} />
        </section>

        <section className="card analytics-card">
          <h2>📊 Analytics</h2>
          <AnalyticsCharts analytics={analytics} />
        </section>

        <section className="card incidents-card">
          <h2>📋 Recent Incidents</h2>
          <table>
            <thead>
              <tr>
                <th>Time</th><th>Animal</th><th>Risk</th><th>Road</th><th>Lighting</th>
              </tr>
            </thead>
            <tbody>
              {incidents.slice(0, 12).map(i => (
                <tr key={i.id} className={`risk-${i.risk_level.toLowerCase()}`}>
                  <td>{new Date(i.timestamp).toLocaleTimeString()}</td>
                  <td>{i.animal_type}</td>
                  <td>{i.risk_level} ({i.risk_score})</td>
                  <td>{i.road_type}</td>
                  <td>{i.lighting}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </div>
  )
}
