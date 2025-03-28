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
          <button
            className="reset-button"
            onClick={() => {
              fetch("http://localhost:8000/api/reset", { method: "POST" })
                .then((res) => res.json())
                .then(() => {
                  // Reinicia el backend y luego recarga la página
                  fetch("http://localhost:8000/api/scenario")
                    .then((res) => res.json())
                    .then((data) => {
                      setScenario(data); // Actualiza el escenario en el frontend
                      window.location.reload(); // Recarga la página para reflejar los cambios
                    })
                    .catch((err) => {
                      console.error("Error fetching new scenario:", err);
                    });
                })
                .catch((err) => {
                  console.error("Error resetting scenario:", err);
                });
            }}
          >
            Nueva conversación
          </button>
        </div>
      ) : (
        <p>Loading scenario...</p>
      )}
    </div>
  );
}
