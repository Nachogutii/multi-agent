import React from "react";
import { useNavigate } from "react-router-dom";
import background from '../background.png';
import "./HomePage.css";
import logo from '../GIG+.png'

export default function HomePage() {
  const navigate = useNavigate();

  const handleStartSimulation = () => {
    fetch("http://localhost:8000/api/reset", { method: "POST" })
      .then(() => {
        localStorage.removeItem("chatMessages");
        navigate("/chat");
      })
      .catch((err) => {
        console.error("Error starting new simulation:", err);
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

        <div className="scenario-card">
          <h2>Copilot Welcome</h2>
          <p>Customer is already using Microsoft 365 and wants to get the most out of Copilot.</p>
          <p><strong>Difficulty:</strong> Intermediate</p>

          <button className="start-button" onClick={handleStartSimulation}>
            Start Simulation
          </button>
        </div>
      </div>
    </div>
  );
}
