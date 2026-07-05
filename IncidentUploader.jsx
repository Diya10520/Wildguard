import { useState } from 'react'

export default function IncidentUploader({ onProcessed }) {
  const [status, setStatus] = useState('')
  const [sightingAnimal, setSightingAnimal] = useState('deer')

  const uploadVideo = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setStatus('Uploading & starting video pipeline...')
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch('/api/detect/video?frame_skip=5', { method: 'POST', body: formData })
    const data = await res.json()
    setStatus(data.note || 'Processing started — watch Live Alerts.')
  }

  const uploadFrame = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setStatus('Analyzing frame...')
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch('/api/detect/frame', { method: 'POST', body: formData })
    const data = await res.json()
    setStatus(`Done — ${data.detections?.length || 0} animal(s) detected.`)
    onProcessed()
  }

  const reportSighting = async () => {
    setStatus('Submitting crowd report...')
    await fetch('/api/report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        animal_type: sightingAnimal,
        lat: 12.9716 + (Math.random() - 0.5) * 0.01,
        lon: 77.5946 + (Math.random() - 0.5) * 0.01,
        reported_by: 'demo_user',
      }),
    })
    setStatus('Sighting reported. Thanks!')
  }

  return (
    <div className="uploader">
      <label className="upload-label">
        📹 Upload dashcam/CCTV video (mock feed)
        <input type="file" accept="video/*" onChange={uploadVideo} />
      </label>

      <label className="upload-label">
        🖼️ Test single frame/image
        <input type="file" accept="image/*" onChange={uploadFrame} />
      </label>

      <div className="sighting-report">
        <select value={sightingAnimal} onChange={e => setSightingAnimal(e.target.value)}>
          <option value="deer">Deer</option>
          <option value="cow">Cow</option>
          <option value="dog">Dog</option>
          <option value="elephant">Elephant</option>
        </select>
        <button onClick={reportSighting}>🌐 Report sighting nearby</button>
      </div>

      {status && <p className="status-line">{status}</p>}
    </div>
  )
}
