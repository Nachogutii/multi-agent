import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./HomePage.css";

export default function HomePage() {
  const [scenarios, setScenarios] = useState({});
  const navigate = useNavigate();

  const linesOfBusiness = [
    {
      id: "copilot",
      title: "Copilot Welcome",
      description: "Copilot Welcome description",
      difficulty: "Beginner",
    },
    {
      id: "proactive",
      title: "Proactive Grace",
      description: "Proactive Grace descrption",
      difficulty: "Intermediate",
    },
  ];

  useEffect(() => {
    Promise.all(
      linesOfBusiness.map((lob) =>
        fetch(`http://localhost:8000/api/scenario/${lob.id}`)
          .then((res) => res.json())
          .then((data) => ({ [lob.id]: data }))
      )
    )
      .then((results) => {
        const merged = Object.assign({}, ...results);
        setScenarios(merged);
      })
      .catch((err) => {
        console.error("Error fetching scenarios:", err);
      });
  }, []);

  const handleStartSimulation = (lobId) => {
    fetch("http://localhost:8000/api/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lob: lobId }),
    })
      .then(() => fetch(`http://localhost:8000/api/scenario/${lobId}`))
      .then((res) => res.json())
      .then((data) => {
        localStorage.removeItem("chatMessages");
        localStorage.setItem("scenario", JSON.stringify(data));
        navigate("/chat");
      })
      .catch((err) => {
        console.error("Error starting simulation:", err);
      });
  };

  const handleNewConversation = (lobId) => {
    fetch("http://localhost:8000/api/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lob: lobId }),
    })
      .then(() => fetch(`http://localhost:8000/api/scenario/${lobId}`))
      .then((res) => res.json())
      .then((data) => {
        setScenarios((prev) => ({ ...prev, [lobId]: data }));
        window.location.reload();
      })
      .catch((err) => {
        console.error("Error resetting scenario:", err);
      });
  };

  return (
    <div className="home-container">
      <h1 className="home-title">GigPlus Customer Simulation</h1>

      <div className="cards-container">
        {linesOfBusiness.map((lob) => {
          const scenario = scenarios[lob.id];
          return (
            <div key={lob.id} className="scenario-card">
              <h2>{lob.title}</h2>
              <p>{lob.description}</p>
              <p>
                <strong>Difficulty:</strong> {lob.difficulty}
              </p>
              {scenario && (
                <p style={{ fontStyle: "italic", marginBottom: "10px" }}>
                  Scenario: {scenario.title}
                </p>
              )}

              <button className="start-button" onClick={() => handleStartSimulation(lob.id)}>
                Start Simulation
              </button>

              <button className="reset-button" onClick={() => handleNewConversation(lob.id)}>
                New Conversation
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
