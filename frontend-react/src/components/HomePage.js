import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./HomePage.css";

export default function HomePage() {
  const [scenario, setScenario] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetch("https://plg-simulator.onrender.com/api/scenario")
      .then((res) => res.json())
      .then((data) => {
        setScenario(data);
      })
      .catch((err) => {
        console.error("Error fetching scenario:", err);
      });
  }, []);

  return (
    <div className="home-container">
      <h1 className="home-title">GigPlus Customer Simulation</h1>

      {scenario ? (
        <div className="scenario-card">
          <h2>{scenario.title}</h2>
          <p>{scenario.description}</p>
          <p><strong>Difficulty:</strong> Intermediate</p>
          <p><strong>Initial Query:</strong> {scenario.initial_query}</p>
          <button className="start-button" onClick={() => navigate("/chat")}>
            Start Simulation
          </button>
        </div>
      ) : (
        <p>Loading scenario...</p>
      )}
    </div>
  );
}
