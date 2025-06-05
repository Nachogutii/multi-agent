import React, { useEffect, useState } from 'react';
import './ScenarioSummaryPage.css';

export default function ScenarioSummaryPage() {
  const [phases, setPhases] = useState([]);

  useEffect(() => {
    const data = localStorage.getItem('scenarioSummary');
    if (data) setPhases(JSON.parse(data));
  }, []);

  return (
    <div className="summary-background">
      <div className="summary-container">
        <h2 className="summary-title">Scenario Summary</h2>
        {phases.length === 0 && <div>No scenario data found.</div>}
        {phases.map((phase, idx) => (
          <div className="summary-phase-card" key={idx}>
            <div className="summary-phase-header">
              <span className="summary-phase-name">{phase.name}</span>
              {phase.icon && <span className="summary-phase-icon">{phase.icon}</span>}
            </div>
            <div className="summary-section">
              <span className="summary-label success-label">On Success goes to:</span>
              <ul>
                {phase.success && phase.success.map((s, i) => <li key={i}>{s}</li>)}
              </ul>
            </div>
            <div className="summary-section">
              <span className="summary-label failure-label">On Failure goes to:</span>
              <ul>
                {phase.failure && phase.failure.map((f, i) => <li key={i}>{f}</li>)}
              </ul>
            </div>
            <div className="summary-section">
              <span className="summary-label">Conditions:</span>
              <ul>
                {phase.conditions && phase.conditions.map((c, i) => <li key={i}>{c}</li>)}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
} 