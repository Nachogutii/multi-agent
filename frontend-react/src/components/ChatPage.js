import React, { useState, useEffect, useRef } from "react";
import * as SpeechSDK from "microsoft-cognitiveservices-speech-sdk";
import { useNavigate } from "react-router-dom";
import './ChatPage.css';

const speechKey = process.env.REACT_APP_SPEECH_KEY;
const speechRegion = process.env.REACT_APP_SPEECH_REGION;

export default function ChatPage() {
  const initialMessages = JSON.parse(localStorage.getItem("chatMessages")) || [];
  const [messages, setMessages] = useState(initialMessages);
  const [userInput, setUserInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [showInfo, setShowInfo] = useState(false);
  const [scenario, setScenario] = useState(null);
  const [isMuted, setIsMuted] = useState(false);
  const synthesizerRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    localStorage.setItem("chatMessages", JSON.stringify(messages));
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const storedScenario = localStorage.getItem("scenario");
    if (storedScenario) {
      setScenario(JSON.parse(storedScenario));
    } else {
      fetch("http://localhost:8000/api/scenario")
        .then((res) => res.json())
        .then((data) => setScenario(data))
        .catch((err) => console.error("Error fetching scenario:", err));
    }
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const speakResponse = (text) => {
    if (isMuted || !speechKey || !speechRegion || !text) return;

    const speechConfig = SpeechSDK.SpeechConfig.fromSubscription(speechKey, speechRegion);
    speechConfig.speechSynthesisVoiceName = "en-US-JennyNeural";
    const audioConfig = SpeechSDK.AudioConfig.fromDefaultSpeakerOutput();
    const synthesizer = new SpeechSDK.SpeechSynthesizer(speechConfig, audioConfig);
    synthesizerRef.current = synthesizer;

    synthesizer.speakTextAsync(
      text,
      () => {
        synthesizer.close();
        if (synthesizerRef.current === synthesizer) {
          synthesizerRef.current = null;
        }
      },
      (err) => {
        console.error("Speech synthesis error:", err);
        synthesizer.close();
        if (synthesizerRef.current === synthesizer) {
          synthesizerRef.current = null;
        }
      }
    );
  };

  const toggleMute = () => {
    const newMuteState = !isMuted;
    setIsMuted(newMuteState);

    if (newMuteState && synthesizerRef.current) {
      synthesizerRef.current.stopSpeakingAsync(() => {
        synthesizerRef.current.close();
        synthesizerRef.current = null;
        console.log("Bot silenciado manualmente.");
      }, (err) => {
        console.error("Error al detener voz:", err);
        synthesizerRef.current?.close();
        synthesizerRef.current = null;
      });
    }
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
        setUserInput(prev => `${prev} ${result.text}`.trim());
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
      const res = await fetch("http://localhost:8000/api/chat", {
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
          {scenario && <h3 className="scenario-title">Copilot Welcome</h3>}
        </div>

        <div className="chat-header-center">
          <h2 className="chat-title">GigPlus Support Chat</h2>
        </div>

        <div className="chat-header-right">
          <button
            className={`mute-button ${isMuted ? 'muted' : ''}`}
            onClick={toggleMute}
            title={isMuted ? "Unmute" : "Mute"}
          >
            {isMuted ? "🔇" : "🔊"}
          </button>
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
            <li><strong>Title:</strong> Microsoft Copilot Satisfaction Check</li>
              <li><strong>Description:</strong> Microsoft is reaching out to Rachel Sanchez, owner of a boutique marketing agency, for a brief (10 min) check-in. She recently began using Copilot and has used Microsoft 365 for 5 years.</li>
              <li><strong>Customer:</strong> Rachel Sanchez<br /><strong>Business:</strong> Boutique brand strategy agency<br /><strong>Tech Level:</strong> Reasonably tech-savvy, time-constrained<br /><strong>Copilot Experience:</strong> 1 month<br /><strong>Communication:</strong> Scheduled phone call (after support email)</li>
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