import { Bar, Doughnut, Line } from 'react-chartjs-2'
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  ArcElement, PointElement, LineElement, Tooltip, Legend
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, PointElement, LineElement, Tooltip, Legend)

export default function AnalyticsCharts({ analytics }) {
  if (!analytics || analytics.total_incidents === 0) {
    return <p className="muted">No data yet — process a video or frame to populate analytics.</p>
  }

  const speciesData = {
    labels: analytics.species_breakdown.map(s => s.animal_type),
    datasets: [{
      label: 'Detections',
      data: analytics.species_breakdown.map(s => s.count),
      backgroundColor: '#457b9d',
    }],
  }

  const riskData = {
    labels: analytics.risk_distribution.map(r => r.risk_level),
    datasets: [{
      data: analytics.risk_distribution.map(r => r.count),
      backgroundColor: ['#e63946', '#f4a261', '#2a9d8f'],
    }],
  }

  const hourlyData = {
    labels: analytics.hourly_activity.map(h => `${h.hour}:00`),
    datasets: [{
      label: 'Activity by hour (UTC)',
      data: analytics.hourly_activity.map(h => h.count),
      borderColor: '#e76f51',
      backgroundColor: 'rgba(231,111,81,0.2)',
      tension: 0.3,
    }],
  }

  return (
    <div className="analytics-grid">
      <div className="chart-box">
        <h4>Species-wise Detections</h4>
        <Bar data={speciesData} options={{ plugins: { legend: { display: false } } }} />
      </div>
      <div className="chart-box">
        <h4>Risk Level Mix</h4>
        <Doughnut data={riskData} />
      </div>
      <div className="chart-box">
        <h4>Peak Activity Times</h4>
        <Line data={hourlyData} options={{ plugins: { legend: { display: false } } }} />
      </div>
      <div className="stat-box">
        <div className="stat-number">{analytics.total_incidents}</div>
        <div className="stat-label">Total Incidents Logged</div>
      </div>
    </div>
  )
}
