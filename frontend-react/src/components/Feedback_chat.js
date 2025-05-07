import React from "react";
import { useNavigate } from "react-router-dom";
import background from '../background.png';
import "./FeedbackChat_copilot.css";

export default function FeedbackChat() {
  const navigate = useNavigate();

  const handleBackToChat = () => {
    localStorage.removeItem("chatMessages");
    navigate("/copilot-chat");
  };

  const feedback = {
    overallScore: 4.6,
    generalFeedback:
      "This was a strong Product-Led Growth conversation. The ambassador successfully leveraged a recent support interaction to re-engage the user and contextualize the value of Copilot Chat. The shift from ChatGPT to Copilot was handled with clarity, and the assistant did well in anchoring product features to specific pain points (access management, file visibility). There was a light-touch, high-trust approach—short, friendly, and benefit-oriented. A slightly tighter loop between discovery and solution could make it even stronger.",
    strength: [
      "✅ Great use of a solved support issue to build trust and transition to value exploration.",
      "✅ Smart positioning of Copilot Chat by comparing it to ChatGPT while highlighting enterprise-specific advantages.",
      "✅ Addressed specific user pain points (file access uncertainty) with clear, actionable value props.",
      "✅ Conversational tone and timing felt low-pressure and respectful of the user's time.",
      "✅ Strong use of phrases like 'real-world tasks' to increase perceived utility of Copilot.",
    ],
    issues: [
      "⚠️ The final pitch was slightly repeated—Copilot Chat's features were described twice (possibly due to copy/paste).",
      "⚠️ Could have asked one follow-up after the 'ChatGPT' mention to deepen understanding of user workflow before pitching.",
    ],
    suggestions: [
      "💡 Try tightening the middle of the conversation to avoid redundancy when transitioning from ChatGPT to Copilot.",
      "💡 Consider adding a small 'next step' CTA beyond the link—like inviting Jamie to try a specific task with Copilot.",
    ],
    training: [
      {
        title: "Get started with Microsoft 365 Copilot Chat",
        url: "https://learn.microsoft.com/en-us/training/modules/get-started-microsoft-365-copilot-business-chat/"
      }
    ]
  };

  const renderList = (title, items) => {
    if (!Array.isArray(items) || items.length === 0) return null;
    return (
      <div className="feedback-section">
        <h3>{title}</h3>
        <ul>
          {items.map((item, idx) => (
            <li key={idx}>
              {typeof item === 'object' && item.url ? (
                <a href={item.url} target="_blank" rel="noopener noreferrer">
                  {item.title}
                </a>
              ) : (
                item
              )}
            </li>
          ))}
        </ul>
      </div>
    );
  };

  return (
    <div
      className="feedbackchat-background"
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
      <div className="feedbackchat-card">
        <h2>Feedback Summary</h2>
        <div className="feedback-score">
          <h3>
            Session overall score: <span>{feedback.overallScore} / 5</span>
          </h3>
        </div>
        <div className="feedback-section">
          <h3>General Feedback</h3>
          <p>{feedback.generalFeedback}</p>
        </div>
        <div className="feedback-lists">
          {renderList("Strengths", feedback.strength)}
          {renderList("Issues", feedback.issues)}
          {renderList("Suggestions", feedback.suggestions)}
          {renderList("Training recommendations", feedback.training)}
        </div>
        <div className="feedbackchat-buttons-row">
          <button onClick={() => navigate("/copilot-chat")} className="feedbackchat-button">
            ← Back to Chat
          </button>
          <button onClick={() => navigate("/")} className="feedbackchat-button">
            ← Back to Lobby
          </button>
        </div>
      </div>
    </div>
  );
}
