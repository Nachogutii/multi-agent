import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./HomePage.css";

export default function HomePage() {
  const [scenario, setScenario] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetch("http://localhost:8000/api/scenario")
      .then((res) => res.json())
      .then((data) => {
        setScenario(data);
      })
      .catch((err) => {
        console.error("Error fetching scenario:", err);
      });
  }, []);

  const handleStartSimulation = () => {
    fetch("http://localhost:8000/api/reset", { method: "POST" })
      .then(() => fetch("http://localhost:8000/api/scenario"))
      .then((res) => res.json())
      .then((data) => {
        localStorage.removeItem("chatMessages");
        localStorage.setItem("scenario", JSON.stringify(data));
        navigate("/chat");
      })
      .catch((err) => {
        console.error("Error starting new simulation:", err);
      });
  };

  const handleNewConversation = () => {
    fetch("http://localhost:8000/api/reset", { method: "POST" })
      .then((res) => res.json())
      .then(() => {
        fetch("http://localhost:8000/api/scenario")
          .then((res) => res.json())
          .then((data) => {
            setScenario(data);
            window.location.reload();
          })
          .catch((err) => {
            console.error("Error fetching new scenario:", err);
          });
      })
      .catch((err) => {
        console.error("Error resetting scenario:", err);
      });
  };

  return (
    <div className="home-container">
      <h1 className="home-title">GigPlus Customer Simulation</h1>

      {scenario ? (
        <div className="scenario-card">
          <h2>{scenario.title}</h2>
          <p>{scenario.description}</p>
          <p><strong>Difficulty:</strong> Intermediate</p>

          <button className="start-button" onClick={handleStartSimulation}>
            Start Simulation
          </button>

          <button className="reset-button" onClick={handleNewConversation}>
            New Conversation
          </button>
        </div>
      ) : (
        <p>Loading scenario...</p>
      )}
    </div>
  );
}
