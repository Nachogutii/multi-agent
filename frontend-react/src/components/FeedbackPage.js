import React, { useEffect, useState, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { submitFeedbackToSupabase } from "../services/feedbackService.js"
import { submitConversationToSupabase } from "../services/submitConversationToSupabase.js"
import "./FeedbackPage.css";

export default function FeedbackPage() {
  const [feedback, setFeedback] = useState(null);
  const navigate = useNavigate();
  const routeLocation = useLocation();
  const effectRan = useRef(false);

  useEffect(() => {
    if (effectRan.current) return;
    effectRan.current = true;
  
    const timestamp = new Date().getTime();
    const path = routeLocation.pathname;
    const sessionId = btoa(`${path}_${timestamp}`).slice(0, 32);
  
    const feedbackKey = `feedback_sent_${sessionId}`;
    const conversationKey = `conversation_sent_${sessionId}`;
  
    const feedbackAlreadySent = localStorage.getItem(feedbackKey);
    const conversationAlreadySent = localStorage.getItem(conversationKey);

    const storedMessages = localStorage.getItem("chatMessages");
    const conversation = storedMessages ? JSON.parse(storedMessages) : [];
  
    if (feedbackAlreadySent && conversationAlreadySent) {
      console.log("✅ Feedback y conversación ya enviados para esta sesión");
      return;
    }
  
    fetch("http://localhost:8000/api/feedback/structured")
      .then((res) => res.json())
      .then((data) => {
        console.log("Structured feedback received:", data);
        setFeedback(data);
  
        if (data?.metrics) {
          submitFeedbackToSupabase({
            ...data,
            sessionId,
          }).then((feedbackId) => {
            localStorage.setItem(feedbackKey, "true");
  
            if (
              feedbackId &&
              conversation.length > 0 &&
              !conversationAlreadySent
            ) {
              submitConversationToSupabase(feedbackId, conversation).then(() => {
                localStorage.setItem(conversationKey, "true");
              });
            }
          });
        }
      })
      .catch((err) => {
        console.error("❌ Error fetching feedback:", err);
        setFeedback({ error: "Error fetching feedback." });
      });
  }, [routeLocation.pathname]);
  
  const renderSection = (title, items, icon, colorClass) => {
    if (!Array.isArray(items) || items.length === 0) return null;
    return (
      <div className={`feedback-card ${colorClass}`}>
        <div className="card-header">
          <span className="card-icon">{icon}</span>
          <h3>{title}</h3>
        </div>
        <ul className="feedback-list">
          {items.map((item, idx) => (
            <li key={idx}>{item}</li>
          ))}
        </ul>
      </div>
    );
  };

  const renderOverallScore = (metrics, customScore) => {
    // Si existe customScore, usamos ese valor, de lo contrario usamos el cálculo original
    if (customScore !== undefined && customScore !== null) {
      // Determinar mensaje basado en la puntuación
      let scoreMessage = "";
      let emoji = "";
      
      if (customScore >= 90) {
        scoreMessage = "Excellent job! Your conversation was outstanding.";
        emoji = "🏆";
      } else if (customScore >= 80) {
        scoreMessage = "Great work! Your conversation skills are impressive.";
        emoji = "🌟";
      } else if (customScore >= 70) {
        scoreMessage = "Good job! You're on the right track.";
        emoji = "👍";
      } else if (customScore >= 60) {
        scoreMessage = "Not bad! With a few improvements, you'll do even better.";
        emoji = "🔍";
      } else {
        scoreMessage = "There's room for improvement. Review the suggestions below.";
        emoji = "📝";
      }
      
      // Renderizar con la puntuación personalizada
      return (
        <div className="feedback-score-card">
          <div className="score-header">
            <h2>
              Conversation Performance
              <span className="custom-score-indicator">*</span>
            </h2>
            <div className="score-emoji">{emoji}</div>
          </div>
          <div className="score-content">
            <div className="score-value">
              <span className="score-number">{customScore}</span>
              <span className="score-max">/100</span>
            </div>
            <p className="score-message">
              {scoreMessage}
            </p>
          </div>
        </div>
      );
    } else {
      // Comportamiento original como fallback
      if (!metrics || typeof metrics !== "object") return null;
      const values = Object.values(metrics);
      if (!values.length) return null;
      const average = (values.reduce((acc, v) => acc + v, 0) / values.length).toFixed(1);
      
      // Determinar mensaje usando la escala original
      let scoreMessage = "";
      let emoji = "";
      
      if (average >= 4.5) {
        scoreMessage = "Excellent job! Your conversation was outstanding.";
        emoji = "🏆";
      } else if (average >= 4.0) {
        scoreMessage = "Great work! Your conversation skills are impressive.";
        emoji = "🌟";
      } else if (average >= 3.5) {
        scoreMessage = "Good job! You're on the right track.";
        emoji = "👍";
      } else if (average >= 3.0) {
        scoreMessage = "Not bad! With a few improvements, you'll do even better.";
        emoji = "🔍";
      } else {
        scoreMessage = "There's room for improvement. Review the suggestions below.";
        emoji = "📝";
      }
      
      // Renderizar con la puntuación original
      return (
        <div className="feedback-score-card">
          <div className="score-header">
            <h2>Conversation Performance</h2>
            <div className="score-emoji">{emoji}</div>
          </div>
          <div className="score-content">
            <div className="score-value">
              <span className="score-number">{average}</span>
              <span className="score-max">/5</span>
            </div>
            <p className="score-message">{scoreMessage}</p>
          </div>
        </div>
      );
    }
  };

  if (!feedback) {
    return (
      <div className="feedback-loading">
        <div className="spinner" />
        <p>Hang tight, we're analyzing your conversation to generate feedback.</p>
        <div className="loading-facts">
          <h4>Did you know?</h4>
          <p>AI-powered feedback analysis can help improve your customer service skills by up to 30%!</p>
        </div>
      </div>
    );
  }
  
  if (feedback.error) return <div className="feedback-error">{feedback.error}</div>;

  return (
    <div className="feedback-page">
      <div className="feedback-header">
        <h1>Your Conversation Feedback</h1>
        <p className="feedback-intro">
          Here's a detailed analysis of your conversation. Use these insights to improve your future interactions.
        </p>
      </div>
      
      {renderOverallScore(feedback.metrics, feedback.custom_score)}
      
      <div className="feedback-sections">
        {renderSection("Key Strengths", feedback.strength, "💪", "strength-card")}
        {renderSection("Improvement Suggestions", feedback.suggestions, "💡", "suggestion-card")}
        {renderSection("Issues to Address", feedback.issues, "⚠️", "issue-card")}
        {renderSection("Training Recommendations", feedback.training, "🎓", "training-card")}
      </div>
      
      <div className="feedback-actions">
        <button onClick={() => navigate("/chat")} className="action-button chat-button">
          <span className="button-icon">💬</span> Back to Chat
        </button>
        <button onClick={() => navigate("/")} className="action-button home-button">
          <span className="button-icon">🏠</span> Back to Lobby
        </button>
      </div>
    </div>
  );
}