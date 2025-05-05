import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import background from '../background.png';
import "./HomePage.css";
import logo from '../GIG+.png';

export default function HomePage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [selectedScenario, setSelectedScenario] = useState('welcome');

  const handleStartSimulation = () => {
    setLoading(true);

    fetch("http://localhost:8000/api/reset", { method: "POST" })
      .then(() => {
        localStorage.removeItem("chatMessages");
        if (selectedScenario === 'chat') {
          navigate("/copilot-chat");
        } else {
          navigate("/chat", { state: { scenario: selectedScenario } });
        }
      })
      .catch((err) => {
        console.error("Error starting new simulation:", err);
        setLoading(false);
      });
  };

  return (
    <div
      className="home-background"
      style={{
        backgroundImage: `url(${background})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
        backgroundAttachment: "fixed",
        minHeight: "100vh",
        width: "100vw",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem",
      }}
    >
      <div className="home-container">
        <div className="home-title-row">
          <img src={logo} alt="GigPlus logo" className="home-logo-inline" />
          <h1 className="home-title">GigPlus Customer Simulation</h1>
        </div>

        <div className="scenarios-container">
          <div
            className={`scenario-card${selectedScenario === 'welcome' ? ' selected' : ''}`}
            onClick={() => setSelectedScenario('welcome')}
            style={{ borderColor: selectedScenario === 'welcome' ? '#0078D4' : 'transparent' }}
          >
            <h2>Copilot Welcome</h2>
            <p>Customer is already using Microsoft 365 and wants to get the most out of Copilot.</p>
            <p><strong>Difficulty:</strong> Intermediate</p>
          </div>

          <div
            className={`scenario-card${selectedScenario === 'chat' ? ' selected' : ''}`}
            onClick={() => setSelectedScenario('chat')}
            style={{ borderColor: selectedScenario === 'chat' ? '#0078D4' : 'transparent' }}
          >
            <h2>Copilot Chat</h2>
            <p>Predefined conversation scenario with hardcoded responses.</p>
            <p><strong>Difficulty:</strong> Beginner</p>
          </div>
        </div>

        <button
          className="start-button"
          onClick={handleStartSimulation}
          disabled={loading}
          style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "2rem" }}
        >
          {loading ? (
            <>
              <span className="spinner" /> Starting simulation...
            </>
          ) : (
            "Start Simulation"
          )}
        </button>
      </div>
    </div>
  );
}
