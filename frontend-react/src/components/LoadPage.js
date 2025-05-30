import React from "react";
import { useNavigate } from "react-router-dom";
import "./LoadPage.css";

const scenarioInfo = {
  1: {
    title: "Copilot Welcome",
    info: [
      { label: "Title:", value: "Microsoft Copilot Satisfaction Check" },
      { label: "Your role:", value: "You are a Copilot Welcome Ambassador" },
      { label: "Case History:", value: "You have been in touch with Rachel via email, and she agreed to a short call" },
      { label: "Your goals:", value: (
        <ul>
          <li>Have a product led growth conversation with Rachel</li>
          <li>Gather Copilot product insights</li>
        </ul>
      ) }
    ]
  },
  2: {
    title: "Copilot Chat",
    info: [
      { label: "Title:", value: "Microsoft 365 Copilot Chat Adoption Outreach" },
      { label: "Your role:", value: "You are a Copilot Chat Ambassador" },
      { label: "Case History:", value: "You contacted Jordan Evans by email and they agreed to a short call" },
      { label: "Your goals:", value: (
        <ul>
          <li>Raise awareness about Microsoft 365 Copilot Chat</li>
          <li>Clarify any doubts about licensing, security, or usability</li>
          <li>Spark interest in trying Copilot Chat through relevant use cases</li>
        </ul>
      ) }
    ]
  }
};

export default function LoadPage() {
  const navigate = useNavigate();
  const scenarioId = parseInt(localStorage.getItem("scenarioId"), 10) || 1;
  const scenario = scenarioInfo[scenarioId];

  const handleBack = () => {
    navigate("/");
  };

  const handleStart = () => {
    navigate("/chat");
  };

  return (
    <div className="loadpage-bg">
      <div className="loadpage-header">
        <div className="loadpage-header-left">
          <span className="loadpage-title-sub">GigPlus Support<br/>Chat Simulation</span>
        </div>
        <div className="loadpage-header-center">
          <span className="loadpage-chat-title">{scenario.title}</span>
        </div>
      </div>
      <div className="loadpage-content">
        <div className="loadpage-info-box">
          <h3>Scenario Information</h3>
          <ul>
            {scenario.info.map((item, idx) => (
              <li key={idx}>
                <strong>{item.label}</strong> {item.value}
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="loadpage-footer">
        <button className="loadpage-back-btn" onClick={handleBack} title="Back to Home">
          Back
        </button>
        <button className="loadpage-start-btn" onClick={handleStart}>
          Start
        </button>
      </div>
    </div>
  );
} 