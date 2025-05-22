import React, { useState, useEffect, useRef } from "react";
import * as SpeechSDK from "microsoft-cognitiveservices-speech-sdk";
import { useNavigate } from "react-router-dom";
import './ChatPage.css';

const speechKey = process.env.REACT_APP_SPEECH_KEY;
const speechRegion = process.env.REACT_APP_SPEECH_REGION;

const typingPhrases = [
  "Thinking",
  "Looking into it",
  "Formulating a response",
  "Just a second"
];

export default function ChatPage() {
  const initialMessages = JSON.parse(localStorage.getItem("chatMessages")) || [];
  const [messages, setMessages] = useState(initialMessages);
  const [userInput, setUserInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [showInfo, setShowInfo] = useState(false);
  const [showCopilotInfo, setShowCopilotInfo] = useState(false);
  const [scenario, setScenario] = useState(null);
  const [isMuted, setIsMuted] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);
  const [showWelcome, setShowWelcome] = useState(true);
  const [isConversationEnded, setIsConversationEnded] = useState(() => {
    return localStorage.getItem("isConversationEnded") === "true";
  });
  const [lastMessageAllowed, setLastMessageAllowed] = useState(false);
  const [typingPhrase, setTypingPhrase] = useState(typingPhrases[0]);
  const [notifications, setNotifications] = useState([]);
  const [isInitialPosition, setIsInitialPosition] = useState(true);
  const synthesizerRef = useRef(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const inputContainerRef = useRef(null);

  useEffect(() => {
    localStorage.setItem("chatMessages", JSON.stringify(messages));
    localStorage.setItem("isConversationEnded", isConversationEnded);
    scrollToBottom();
  }, [messages, isConversationEnded]);

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
    if (messages.length === 0) {
      setMessages([{
        sender: "bot",
        text: "👋 Welcome! Before you start, click the ℹ️ info button (top right) to get key instructions.",
        isWelcome: true
      }]);
    }
  }, []);

  useEffect(() => {
    if (!messages.some(msg => msg.isWelcome)) {
      const showTooltipInterval = setInterval(() => {
        setShowTooltip(true);
        const hideTimeout = setTimeout(() => {
          setShowTooltip(false);
        }, 5000);
        return () => clearTimeout(hideTimeout);
      }, 15000);
      return () => clearInterval(showTooltipInterval);
    }
  }, [messages]);

  useEffect(() => {
    let phraseInterval;
    if (loading) {
      let phraseIndex = 0;
      setTypingPhrase(typingPhrases[phraseIndex]);
      phraseInterval = setInterval(() => {
        phraseIndex = (phraseIndex + 1) % typingPhrases.length;
        setTypingPhrase(typingPhrases[phraseIndex]);
      }, 5000);
    }
    return () => {
      if (phraseInterval) {
        clearInterval(phraseInterval);
      }
    };
  }, [loading]);

  useEffect(() => {
    if (textareaRef.current && inputContainerRef.current) {
      textareaRef.current.style.height = '40px'; 
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
      inputContainerRef.current.style.height = (textareaRef.current.scrollHeight + 24) + 'px'; 
    }
  }, [userInput]);

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

  const addNotification = (message, type = 'info') => {
    const id = Date.now();
    setNotifications(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setNotifications(prev => prev.filter(notification => notification.id !== id));
    }, 5000);
  };

  const handleTextareaChange = (e) => {
    setUserInput(e.target.value);
  };

  const handleTextareaKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(e);
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!userInput.trim() || loading) return;
    if (messages.length === 1 && messages[0].isWelcome) {
      setMessages([]);
      setIsInitialPosition(false);
    }
    const newMessage = { sender: "user", text: userInput };
    setMessages((prev) => [...prev, newMessage]);
    setLoading(true);
    setUserInput("");
    if (textareaRef.current && inputContainerRef.current) {
      textareaRef.current.style.height = '40px';
      inputContainerRef.current.style.height = '';
    }
    try {
      const res = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: userInput, phase: "exploration" })
      });
      const data = await res.json();
      const responseLower = data.response.toLowerCase();
      console.log("Checking response for banners:", responseLower);
      if (responseLower.includes("demo") || responseLower.includes("show me")) {
        console.log("Demo detected - showing success banner");
        addNotification("🎯 Business goal achieved: User requested a demo", "success");
      }
      if (responseLower.includes("feedback") || responseLower.includes("helpful") || responseLower.includes("using it")) {
        console.log("Feedback detected - showing info banner");
        addNotification("📝 Customer feedback noted: Product insights gathered", "info");
      }
      if (responseLower.includes("not ready") || responseLower.includes("later")) {
        console.log("Not ready detected - showing warning banner");
        addNotification("📝 Customer feedback noted: They're not ready to buy yet", "warning");
      }
      if (data.phase && (data.phase.includes("closure") || data.phase === "Conversation End")) {
        if (!lastMessageAllowed) {
          setLastMessageAllowed(true);
        } else {
          setIsConversationEnded(true);
        }
      }
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
    setLoading(false);
  };

  const navigate = useNavigate();

  const handleFeedbackClick = () => {
    navigate("/feedback");
  };

  const handleReset = () => {
    setMessages([]);
    setIsConversationEnded(false);
    setLastMessageAllowed(false);
    localStorage.removeItem("chatMessages");
    localStorage.removeItem("isConversationEnded");
  };

  // Botón dinámico
  const renderDynamicButton = () => {
    if (listening) {
      // Grabando: micrófono rojo animado
      return (
        <button
          type="button"
          className="dynamic-button recording"
          onClick={() => {}}
          disabled={loading}
          tabIndex={0}
        >
          <img src="/speak.png" alt="Recording" className="icon recording-icon" />
        </button>
      );
    } else if (userInput.trim().length > 0) {
      // Hay texto: mostrar send
      return (
        <button
          type="submit"
          className="dynamic-button"
          disabled={loading}
          tabIndex={0}
        >
          <img src="/send.png" alt="Send" className="icon" />
        </button>
      );
    } else {
      // Por defecto: micrófono
      return (
        <button
          type="button"
          className="dynamic-button"
          onClick={recognizeSpeech}
          disabled={loading}
          tabIndex={0}
        >
          <img src="/speak.png" alt="Speak" className="icon" />
        </button>
      );
    }
  };

  return (
    <div className="chat-container">
      <div className="notification-container">
        {notifications.map(notification => (
          <div key={notification.id} className={`notification-banner ${notification.type}`}>
            <span className="notification-icon">{notification.message.split(' ')[0]}</span>
            <span className="notification-message">{notification.message}</span>
          </div>
        ))}
      </div>
      <div className="chat-header">
        <div className="chat-header-left">
          {scenario && <h3 className="scenario-title">Copilot Welcome</h3>}
        </div>
        <div className="chat-header-center">
          <h2 className="chat-title">GigPlus Support Chat Simulation</h2>
        </div>
        <div className="chat-header-right">
          <button
            className={`mute-button ${isMuted ? 'muted' : ''}`}
            onClick={toggleMute}
            title={isMuted ? "Unmute" : "Mute"}
          >
            {isMuted ? "🔇" : "🔊"}
          </button>
          <div className="info-button-container">
            {showTooltip && !messages.some(msg => msg.isWelcome) && (
              <div className="info-tooltip">
                👉 Need to recall the task?
              </div>
            )}
            {!messages.some(msg => msg.isWelcome) && (
              <button className="info-button" onClick={() => setShowInfo(true)}>i</button>
            )}
          </div>
        </div>
      </div>
      <div className="messages-container">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`message ${msg.sender === "user" ? "user-message" : "bot-message"}`}
            data-welcome={msg.isWelcome ? "true" : "false"}
          >
            <div className="message-content">
              <p>
                {msg.text}
                {msg.isWelcome && (
                  <button 
                    className="welcome-info-button" 
                    onClick={() => setShowInfo(true)}
                    title="Show instructions"
                  >
                    i
                  </button>
                )}
              </p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="message bot-message">
            <div className="typing-indicator">
              <span className="typing-text">Typing</span>
              <span className="typing-dots"></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form 
        className={`input-container ${isInitialPosition ? 'initial-position' : 'moved'}`} 
        onSubmit={sendMessage}
        ref={inputContainerRef}
      >
        <div className="copilot-logo-container">
          <img 
            src="/copilot_logo.png" 
            alt="Copilot Logo" 
            className="copilot-logo" 
            onClick={() => setShowCopilotInfo(true)}
          />
        </div>
        {!isConversationEnded ? (
          <>
            <textarea
              ref={textareaRef}
              className="message-input"
              value={userInput}
              onChange={handleTextareaChange}
              onKeyDown={handleTextareaKeyDown}
              placeholder={loading ? "Waiting for response..." : "Type your message..."}
              disabled={loading}
              rows={1}
              style={{ minHeight: '40px', resize: 'none', overflowY: 'auto', fontFamily: 'inherit' }}
            />
            {renderDynamicButton()}
          </>
        ) : (
          <div className="conversation-ended-message">
            Conversation ended. Thank you for your time!
          </div>
        )}
        <button
          type="button"
          className="feedback-button"
          onClick={handleFeedbackClick}
        >
          Feedback
        </button>
      </form>
      {showCopilotInfo && (
        <>
          <div className="popup-overlay" onClick={() => setShowCopilotInfo(false)} />
          <div className="popup">
            <h3>Chat Controls</h3>
            <ul>
              <li>🎤 <strong>Speak:</strong> Write your message by voice</li>
              <li>📝 <strong>Send:</strong> Send your message</li>
              <li>📊 <strong>Feedback:</strong> Go to feedback page</li>
              <li>ℹ️ <strong>Info:</strong> Show chat objectives</li>
              <li>🔊 <strong>Mute:</strong> Toggle bot voice</li>
            </ul>
            <button onClick={() => setShowCopilotInfo(false)} className="popup-close-button">
              Close
            </button>
          </div>
        </>
      )}
      {showInfo && scenario && (
        <>
          <div className="popup-overlay" onClick={() => setShowInfo(false)} />
          <div className="popup">
            <h3>Scenario Information</h3>
            <ul>
              <li><strong>Title:</strong> Microsoft Copilot Satisfaction Check</li>
              <li><strong>• Your role:</strong> You are a Copilot Welcome Ambassador<br /><strong>• Case History:</strong> You have been in touch with Rachel via email, and she agreed to a short call<p/><strong>• Your goals:</strong><br />• Have a product led growth conversation with Rachel<br />• Gather Copilot product insights</li>
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