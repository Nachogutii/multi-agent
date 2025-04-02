import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./FeedbackPage.css";

export default function FeedbackPage() {
  const [feedback, setFeedback] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetch("http://localhost:8000/api/feedback")
      .then((res) => res.json())
      .then((data) => {
        console.log("✅ Feedback fetched:", data);
        setFeedback(data.feedback); // << acceder a feedback anidado
      })
      .catch((err) => {
        console.error("❌ Error fetching feedback:", err);
        setFeedback({ error: "Error fetching feedback." });
      });
  }, []);

  const renderList = (title, items) => {
    if (!Array.isArray(items) || items.length === 0) return null;

    return (
      <div className="feedback-section">
        <h3>{title}</h3>
        <ul>
          {items.map((item, idx) => (
            <li key={idx}>{item}</li>
          ))}
        </ul>
      </div>
    );
  };

  const renderPhaseScores = (scores) => {
    if (!scores) return null;
    return (
      <div className="feedback-section">
        <h3>Phase Scores</h3>
        <ul>
          {Object.entries(scores).map(([phase, value], idx) => (
            <li key={idx}>
              <strong>{phase.replaceAll("_", " ")}:</strong> {value}/20
            </li>
          ))}
        </ul>
      </div>
    );
  };

  if (!feedback || feedback.error) {
    return (
      <div className="feedback-page">
        <h2>Conversation Feedback</h2>
        <p>{feedback?.error || "Loading..."}</p>
      </div>
    );
  }

  return (
    <div className="feedback-page">
      <h2>Conversation Feedback</h2>

      {feedback.score && (
        <div className="feedback-section">
          <h3>Overall Score</h3>
          <p>{feedback.score} / 100</p>
        </div>
      )}

      {renderPhaseScores(feedback.phase_scores)}
      {renderList("Key Strengths", feedback.strengths)}
      {renderList("Areas for Improvement", feedback.feedback)}
      {renderList("Suggestions", feedback.suggestions)}
      {renderList("Missed Opportunities", feedback.missed_opportunities)}
      {renderList("Customer Objections", feedback.objections)}
      {renderList("Pain Points", feedback.pain_points)}
      {renderList("Blockers", feedback.blockers)}

      <button onClick={() => navigate("/chat")} className="back-button">
        ← Back to Chat
      </button>
    </div>
  );
}
