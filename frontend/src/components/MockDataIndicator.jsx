import './MockDataIndicator.css'

function MockDataIndicator() {
  return (
    <div className="mock-data-indicator">
      <span className="indicator-icon">🎭</span>
      <span className="indicator-text">Using Mock Data</span>
      <span className="indicator-hint">(Backend not connected - showing demo data)</span>
    </div>
  )
}

export default MockDataIndicator

