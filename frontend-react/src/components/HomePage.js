import React from 'react';
import { useNavigate } from 'react-router-dom';
import './HomePage.css';
import logo from '../GIG+.png';

export default function HomePage() {
  const navigate = useNavigate();
  const [loadingStates, setLoadingStates] = useState({
    welcome: false,
    copilot: false
  });

  const handleStartSimulation = (scenarioType) => {
    setLoadingStates(prev => ({
      ...prev,
      [scenarioType]: true
    }));

    let scenarioId = 1;
    if (scenarioType === 'copilot') {
      scenarioId = 2;
    }

    fetch("https://plg-simulator.onrender.com/api/reset", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ id: scenarioId })
    })
      .then(() => {
        localStorage.setItem("scenarioId", scenarioId);
        localStorage.removeItem("chatMessages");
        localStorage.removeItem("isConversationEnded");
        navigate("/chat");
      })
      .catch((err) => {
        console.error("Error starting new simulation:", err);
        setLoadingStates(prev => ({
          ...prev,
          [scenarioType]: false
        }));
      });
  };

  return (
    <div className="home-background">
      <div className="home-container">
        <div className="home-title-row">
          <img src={logo} alt="GigPlus logo" className="home-logo-inline" />
          <h1 className="home-title">GigPlus Customer Simulation</h1>
        </div>

        <div className="scenarios-container">
        <div className="scenario-card">
          <h2>Copilot Welcome</h2>
          <p>Customer is already using Microsoft 365 and wants to get the most out of Copilot.</p>
          <p><strong>Difficulty:</strong> Intermediate</p>

          <button
            className="start-button"
              onClick={() => handleStartSimulation('welcome')}
              disabled={loadingStates.welcome || loadingStates.copilot}
            style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}
          >
              {loadingStates.welcome ? (
              <>
                Starting simulation... <span className="spinner" />
              </>
            ) : (
              "Start Simulation"
            )}
          </button>
          </div>

          <div className="scenario-card">
            <h2>Copilot Chat</h2>
            <p>Help a Microsoft 365 user understand and adopt Copilot Chat by addressing doubts and demonstrating its value through relevant use cases.</p>
            <p><strong>Difficulty:</strong> Easy</p>

            <button
              className="start-button"
              onClick={() => handleStartSimulation('copilot')}
              disabled={loadingStates.welcome || loadingStates.copilot}
              style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}
            >
              {loadingStates.copilot ? (
                <>
                  Starting simulation... <span className="spinner" />
                </>
              ) : (
                "Start Simulation"
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
