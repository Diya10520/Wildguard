export default function AlertPanel({ alerts }) {
  const speak = (text) => {
    if ('speechSynthesis' in window) {
      const utter = new SpeechSynthesisUtterance(text)
      utter.rate = 1.05
      window.speechSynthesis.speak(utter)
    }
  }

  return (
    <div className="alert-panel">
      {alerts.length === 0 && <p className="muted">No alerts yet — run a detection to see live alerts here.</p>}
      {alerts.map((a, idx) => {
        if (a.type === 'detection') {
          return (
            <div key={idx} className={`alert-item level-${a.incident.risk_level.toLowerCase()}`}>
              <div className="alert-text">{a.alert}</div>
              <div className="alert-meta">
                Risk: {a.incident.risk_level} ({a.incident.risk_score}) · ETA {a.time_to_reach_s}s
              </div>
            </div>
          )
        }
        if (a.type === 'emergency') {
          speak(a.message)
          return (
            <div key={idx} className="alert-item level-high emergency">
              🚨 {a.message}
            </div>
          )
        }
        if (a.type === 'crowd_report') {
          return (
            <div key={idx} className="alert-item level-info">
              {a.message}
            </div>
          )
        }
        return (
          <div key={idx} className="alert-item level-info">{a.message}</div>
        )
      })}
    </div>
  )
}
