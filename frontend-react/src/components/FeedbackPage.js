import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import './FeedbackPage.css';

export default function FeedbackPage() {
  const [feedbackData, setFeedbackData] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetch("http://localhost:8000/api/feedback")
      .then((res) => res.json())
      .then((data) => setFeedbackData(data))
      .catch((err) => setFeedbackData({ feedback: "Error fetching feedback." }));
  }, []);

  const parseSection = (title, text) => {
    const sectionRegex = new RegExp(`${title}:(.*?)(\\n[A-Z]|$)`, 's');
    const match = text.match(sectionRegex);
    if (!match) return null;

    const content = match[1]
      .split("\n")
      .map(line => line.trim())
      .filter(line => line && !line.startsWith(title));

    return (
      <div className="feedback-section">
        <h3>{title}</h3>
        <ul>
          {content.map((item, idx) => (
            <li key={idx}>{item.replace(/^• /, '').replace(/^✓ /, '✅ ').replace(/^✗ /, '❌ ')}</li>
          ))}
        </ul>
      </div>
    );
  };

  if (!feedbackData) {
    return (
      <div className="feedback-page">
        <h2>Conversation Feedback</h2>
        <p>Loading...</p>
      </div>
    );
  }

  const fullText = feedbackData.feedback || "";

  return (
    <div className="feedback-page">
      <h2>Conversation Feedback</h2>

      <div className="feedback-section">
        <h3>Overall Score</h3>
        <p>{fullText.match(/Overall Score:.*\n/)?.[0]?.replace("Overall Score:", "").trim()}</p>
      </div>

      {parseSection("Phase Coverage", fullText)}
      {parseSection("Phase Transitions", fullText)}
      {parseSection("Key Strengths", fullText)}
      {parseSection("Areas for Improvement", fullText)}
      {parseSection("Recommendations", fullText)}
      {parseSection("Customer Objections", fullText)}

      <button onClick={() => navigate("/")} className="back-button">← Back to Chat</button>
    </div>
  );
}
