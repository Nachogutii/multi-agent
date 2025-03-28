import React, { useState, useEffect, useRef } from "react";
import * as SpeechSDK from "microsoft-cognitiveservices-speech-sdk";
import { useNavigate } from "react-router-dom";
import './ChatPage.css';

const speechKey = process.env.REACT_APP_SPEECH_KEY;
const speechRegion = process.env.REACT_APP_SPEECH_REGION;

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [showInfo, setShowInfo] = useState(false);
  const [scenario, setScenario] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    fetch("https://plg-simulator.onrender.com/api/scenario")
      .then((res) => res.json())
      .then((data) => setScenario(data))
      .catch((err) => console.error("Error fetching scenario:", err));
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const speakResponse = (text) => {
    if (!speechKey || !speechRegion || !text) return;
    const speechConfig = SpeechSDK.SpeechConfig.fromSubscription(speechKey, speechRegion);
    speechConfig.speechSynthesisVoiceName = "en-US-JennyNeural";
    const audioConfig = SpeechSDK.AudioConfig.fromDefaultSpeakerOutput();
    const synthesizer = new SpeechSDK.SpeechSynthesizer(speechConfig, audioConfig);

    synthesizer.speakTextAsync(
      text,
      () => synthesizer.close(),
      (err) => {
        console.error("Speech synthesis error:", err);
        synthesizer.close();
      }
    );
  };

  const recognizeSpeech = async () => {
    if (!speechKey || !speechRegion) return;
    setListening(true);

    const speechConfig = SpeechSDK.SpeechConfig.fromSubscription(speechKey, speechRegion);
    speechConfig.speechRecognitionLanguage = "en-US";
    const audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();
    const recognizer = new SpeechSDK.SpeechRecognizer(speechConfig, audioConfig);

    recognizer.recognizeOnceAsync(result => {
      setListening(false);
      if (result.reason === SpeechSDK.ResultReason.RecognizedSpeech) {
        setUserInput(result.text);
      } else {
        console.error("Speech not recognized.");
      }
      recognizer.close();
    }, err => {
      setListening(false);
      console.error("Speech recognition error:", err);
      recognizer.close();
    });
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!userInput.trim()) return;

    const newMessage = { sender: "user", text: userInput };
    setMessages((prev) => [...prev, newMessage]);
    setLoading(true);

    try {
      const res = await fetch("https://plg-simulator.onrender.com/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: userInput, phase: "exploration" })
      });
      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: data.response }
      ]);
      speakResponse(data.response);
    } catch (err) {
      console.error("Error connecting to backend:", err);
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Error connecting to the backend." }
      ]);
    }

    setUserInput("");
    setLoading(false);
  };

  const navigate = useNavigate(); 

  const handleFeedbackClick = () => {
    navigate("/feedback"); 
  };


  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="chat-header-left">
          {scenario && <h3 className="scenario-title">{scenario.title}</h3>}
        </div>

        <div className="chat-header-center">
          <h2 className="chat-title">GigPlus Support Chat</h2>
        </div>

        <div className="chat-header-right">
          <button className="info-button" onClick={() => setShowInfo(true)}>i</button>
        </div>
      </div>

      <div className="messages-container">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`message ${msg.sender === "user" ? "user-message" : "bot-message"}`}
          >
            <div className="message-content">
              <p>{msg.text}</p>
            </div>
          </div>
        ))}
        {loading && <p className="bot-message">Typing...</p>}
        <div ref={messagesEndRef} />
      </div>

      <form className="input-container" onSubmit={sendMessage}>
      <input
        type="text"
        className="message-input"
        value={userInput}
        onChange={(e) => setUserInput(e.target.value)}
        placeholder="Type your message..."
      />
      <button
        type="button"
        className={`voice-button ${listening ? 'listening' : ''}`}
        onClick={recognizeSpeech}
        disabled={loading || listening}
      >
        Speak
      </button>
      <button type="submit" className="send-button">
        Send
      </button>
      <button
        type="button"
        className="feedback-button"
        onClick={handleFeedbackClick}
      >
        Feedback
      </button>
      </form>


      {showInfo && scenario && (
        <>
          <div className="popup-overlay" onClick={() => setShowInfo(false)} />
          <div className="popup">
            <h3>Scenario Information</h3>
            <ul>
              <li><strong>Title:</strong> {scenario.title}</li>
              <li><strong>Description:</strong> {scenario.description}</li>
              <li><strong>Initial Query:</strong> {scenario.initial_query}</li>
            </ul>
            <button onClick={() => setShowInfo(false)} className="popup-close-button">
              Close
            </button>
          </div>
        </>
      )}
    </div>
  );
}
