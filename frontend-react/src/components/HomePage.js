import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import background from '../background.png';
import "./HomePage.css";
import logo from '../GIG+.png';

export default function HomePage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState(null);

  useEffect(() => {
    // Fetch scenarios when component mounts
    fetch("http://localhost:8000/api/scenarios")
      .then(response => response.json())
      .then(data => {
        setScenarios(data);
        if (data.length > 0) {
          setSelectedScenario(data[0].id);
        }
      })
      .catch(err => {
        console.error("Error fetching scenarios:", err);
      });
  }, []);

  const handleStartSimulation = () => {
    if (!selectedScenario) return;

    setLoading(true);

    // Clean up any existing session
    localStorage.removeItem("currentSessionId");
    
    // Generate a session ID that will be consistent throughout the chat and feedback
    const timestamp = new Date().getTime();
    const sessionId = btoa(`/chat_${timestamp}`).slice(0, 32);
    localStorage.setItem("currentSessionId", sessionId);

    fetch("http://localhost:8000/api/reset", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ id: selectedScenario })
    })
      .then(() => {
        localStorage.setItem("scenarioId", selectedScenario);
        localStorage.removeItem("chatMessages");
        localStorage.removeItem("isConversationEnded");
        navigate("/chat");
      })
      .catch((err) => {
        console.error("Error starting new simulation:", err);
        setLoading(false);
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
          <div className="scenario-selector">
            <select 
              className="scenario-dropdown"
              value={selectedScenario || ""}
              onChange={(e) => setSelectedScenario(Number(e.target.value))}
            >
              {scenarios.map(scenario => (
                <option key={scenario.id} value={scenario.id}>
                  {scenario.name}
                </option>
              ))}
            </select>

            <button
              className="start-button"
              onClick={handleStartSimulation}
              disabled={loading || !selectedScenario}
              style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}
            >
              {loading ? (
                <>
                  Starting simulation... <span className="spinner" />
                </>
              ) : (
                "Start Simulation"
              )}
            </button>
          </div>

          <button
            className="creator-button"
            onClick={() => navigate('/create-scenario')}
          >
            Create New Scenario
          </button>
        </div>
      </div>
    </div>
  );
}
