import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import background from '../background.png';
import "./HomePage.css";
import logo from '../GIG+.png'

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

        {scenario ? (
          <div className="scenario-card">
            <h2>Copilot Welcome</h2>
            <p>Customer is already using some Microsoft products and wants to know more about Copilot.</p>
            <p><strong>Difficulty:</strong> Intermediate</p>

            <button className="start-button" onClick={handleStartSimulation}>
              Start Simulation
            </button>

            {/*
            <button className="reset-button" onClick={handleNewConversation}>
              New Conversation
            </button>*/}
            
          </div>
        ) : (
          <p>Loading scenario...</p>
        )}
      </div>
    </div>
  );
}