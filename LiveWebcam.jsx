import { useEffect, useRef, useState } from 'react'

// Captures frames from the user's webcam every INTERVAL_MS and sends them
// to the backend for detection — this is the "live CCTV/dashcam simulation"
// in action, no video file needed for the demo.
const INTERVAL_MS = 2000

export default function LiveWebcam({ onProcessed }) {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)
  const [running, setRunning] = useState(false)
  const [lastResult, setLastResult] = useState('')

  const start = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true })
      streamRef.current = stream
      videoRef.current.srcObject = stream
      setRunning(true)
    } catch (err) {
      setLastResult('Camera access denied or unavailable.')
    }
  }

  const stop = () => {
    streamRef.current?.getTracks().forEach(t => t.stop())
    setRunning(false)
  }

  useEffect(() => {
    if (!running) return
    const interval = setInterval(async () => {
      const video = videoRef.current
      const canvas = canvasRef.current
      if (!video || !canvas || video.readyState < 2) return

      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext('2d')
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

      canvas.toBlob(async (blob) => {
        if (!blob) return
        const formData = new FormData()
        formData.append('file', blob, 'frame.jpg')
        try {
          const res = await fetch('/api/detect/frame', { method: 'POST', body: formData })
          const data = await res.json()
          const count = data.detections?.length || 0
          setLastResult(count > 0
            ? `Detected: ${data.detections.map(d => d.label).join(', ')}`
            : 'No animals in frame.')
          if (count > 0) onProcessed()
        } catch (e) {
          setLastResult('Backend not reachable.')
        }
      }, 'image/jpeg', 0.8)
    }, INTERVAL_MS)

    return () => clearInterval(interval)
  }, [running, onProcessed])

  useEffect(() => () => stop(), [])

  return (
    <div className="live-webcam">
      <video ref={videoRef} autoPlay muted playsInline className="webcam-video" />
      <canvas ref={canvasRef} style={{ display: 'none' }} />
      <div className="webcam-controls">
        {!running
          ? <button onClick={start}>🎥 Start Live Camera Detection</button>
          : <button onClick={stop} className="stop-btn">⏹ Stop</button>}
      </div>
      {lastResult && <p className="status-line">{lastResult}</p>}
    </div>
  )
}
