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
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
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
  const [isInitialPosition, setIsInitialPosition] = useState(() => {
    return initialMessages.length === 0 || (initialMessages.length === 1 && initialMessages[0].isWelcome);
  });
  // Estados para el modo admin
  const [isAdminMode, setIsAdminMode] = useState(false);
  const [isAdminPanelOpen, setIsAdminPanelOpen] = useState(false);
  const [currentPhase, setCurrentPhase] = useState(null);
  const [currentConditions, setCurrentConditions] = useState(null);
  const [currentObservations, setCurrentObservations] = useState(null);
  const [conditionsForNextPhases, setConditionsForNextPhases] = useState([]);
  const synthesizerRef = useRef(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const inputContainerRef = useRef(null);

  useEffect(() => {
    localStorage.setItem("chatMessages", JSON.stringify(messages));
    localStorage.setItem("isConversationEnded", isConversationEnded);
  }, [messages, isConversationEnded]);

  useEffect(() => {
    // Verificar parámetro de URL para modo admin
    const searchParams = new URLSearchParams(window.location.search);
    if (searchParams.get("admin_pswrd") === "helloworld") {
      setIsAdminMode(true);
    }

    const storedScenarioId = localStorage.getItem("scenarioId");
    if (storedScenarioId) {
      const parsedScenarioId = parseInt(storedScenarioId, 10);
      console.log("Scenario ID:", parsedScenarioId);
      setScenario({ id: parsedScenarioId });
    } else {
      fetch("http://localhost:8000/api/scenario")
        .then((res) => res.json())
        .then((data) => setScenario(data))
        .catch((err) => console.error("Error fetching scenario:", err));
    }
    if (messages.length === 0) {
      setMessages([{
        sender: "bot",
        text: "👋 Welcome! Before you start, click the info button to get key instructions.",
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
      }, 25000);
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
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ 
        behavior: "smooth",
        block: "end"
      });
    }
  };

  useEffect(() => {
    const messagesContainer = document.querySelector('.messages-container');
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }, [messages]);

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
      
      // Actualizar estados del modo admin
      setCurrentPhase(data.phase);
      setCurrentConditions(data.feedback?.accumulated_conditions);
      setCurrentObservations(data.feedback?.observations);
      setConditionsForNextPhases(data.feedback?.conditions_for_next_phases || []);
      
      console.log("Checking response for banners:", responseLower);
      if (responseLower.includes("demo") || responseLower.includes("show me")) {
        console.log("Demo detected - showing success banner");
        addNotification("Business goal achieved: User requested a demo", "success");
      }
      if (responseLower.includes("feedback") || responseLower.includes("helpful") || responseLower.includes("using it")) {
        console.log("Feedback detected - showing info banner");
        addNotification("Customer feedback noted: Product insights gathered", "info");
      }
      if (responseLower.includes("not ready") || responseLower.includes("later")) {
        console.log("Not ready detected - showing warning banner");
        addNotification("Customer feedback noted: They're not ready to buy yet", "warning");
      }
      if (data.phase && (data.phase.includes("closure") || data.phase === "Conversation End")) {
        setIsConversationEnded(true);
      }
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: data.response }
      ]);
      speakResponse(data.response);
      scrollToBottom();
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

  const handleTitleClick = () => {
    setShowConfirmDialog(true);
  };

  const handleConfirmNavigation = () => {
    setShowConfirmDialog(false);
    navigate("/");
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

  const canUseFeedback = () => {
    const userMessages = messages.filter(msg => msg.sender === "user").length;
    return isConversationEnded || userMessages >= 3;
  };

  const getChatTitle = () => {
    if (scenario) {
      if (scenario.id === 1) {
        return "Copilot Welcome";
      } else if (scenario.id === 2) {
        return "Copilot Chat";
      }
    }
    return "Chat"; // Título por defecto
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
          {scenario && <h3 className="scenario-title">GigPlus Support Chat Simulation</h3>}
        </div>
        <div className="chat-header-center">
          <h2 className="chat-title" onClick={handleTitleClick}>{getChatTitle()}</h2>
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
                Need to recall the task?
              </div>
            )}
            {!messages.some(msg => msg.isWelcome) && (
              <button className="info-button" onClick={() => setShowInfo(true)}>i</button>
            )}
          </div>
        </div>
      </div>
      {isAdminMode && (
        <>
          <button 
            className={`admin-toggle ${isAdminPanelOpen ? 'open' : ''}`}
            onClick={() => setIsAdminPanelOpen(!isAdminPanelOpen)}
          >
            {isAdminPanelOpen ? 'Close Admin Panel' : 'Open Admin Panel'}
          </button>
          <div className={`admin-panel ${isAdminPanelOpen ? 'open' : ''}`}>
            <h4>
              Admin Info
              <span className="admin-badge">ADMIN MODE</span>
            </h4>
            <div className="admin-panel-section">
              <strong>Current Phase:</strong>
              <p>{currentPhase || 'N/A'}</p>
            </div>
            <div className="admin-panel-section">
              <strong>Accumulated Conditions:</strong>
              {currentConditions && currentConditions.length > 0 ? (
                <ul>
                  {currentConditions.map((condition, index) => (
                    <li key={index}>{typeof condition === 'object' ? JSON.stringify(condition) : condition}</li>
                  ))}
                </ul>
              ) : (
                <p>None</p>
              )}
            </div>
            <div className="admin-panel-section">
              <strong>Conditions to Achieve Next Phases:</strong>
              {conditionsForNextPhases && conditionsForNextPhases.length > 0 ? (
                conditionsForNextPhases.map((phaseInfo, index) => (
                  <div key={index} style={{ marginTop: '10px' }}>
                    <strong style={{ color: phaseInfo.type === 'success' ? 'lightgreen' : 'lightcoral' }}>
                      Next {phaseInfo.type} phase: {phaseInfo.next_phase_name}
                    </strong>
                    {phaseInfo.conditions_to_meet && phaseInfo.conditions_to_meet.length > 0 ? (
                      <ul>
                        {phaseInfo.conditions_to_meet.map((condition, cIndex) => (
                          <li key={cIndex}>{typeof condition === 'object' ? JSON.stringify(condition) : condition}</li>
                        ))}
                      </ul>
                    ) : (
                      <p>No specific conditions listed for this phase.</p>
                    )}
                  </div>
                ))
              ) : (
                <p>No upcoming phase conditions available.</p>
              )}
            </div>
          </div>
        </>
      )}
      <div className={`messages-container ${isAdminMode ? 'with-admin' : ''} ${isAdminMode && !isAdminPanelOpen ? 'collapsed' : ''}`}>
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
        className={`input-container ${isInitialPosition ? 'initial-position' : 'moved'} ${isAdminMode ? 'with-admin' : ''} ${isAdminMode && !isAdminPanelOpen ? 'collapsed' : ''}`} 
        onSubmit={sendMessage}
        ref={inputContainerRef}
      >
        {!isConversationEnded ? (
          <>
            <div className="input-top-row">
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
            </div>
            <div className="input-bottom-row">
              <div className="copilot-logo-container">
                <img 
                  src="/copilot_logo.png" 
                  alt="Copilot Logo" 
                  className="copilot-logo" 
                  onClick={() => setShowCopilotInfo(true)}
                />
              </div>
              <div className="right-buttons">
                {renderDynamicButton()}
                <button
                  type="button"
                  className={`feedback-button ${canUseFeedback() ? 'enabled' : ''}`}
                  onClick={canUseFeedback() ? handleFeedbackClick : undefined}
                >
                  Feedback
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="conversation-ended-container">
            <div className="conversation-ended-message">
              Conversation ended. Thank you for your time!
            </div>
            <button
              type="button"
              className="feedback-button enabled"
              onClick={handleFeedbackClick}
            >
              Feedback
            </button>
          </div>
        )}
      </form>
      {showCopilotInfo && (
        <>
          <div className="popup-overlay" onClick={() => setShowCopilotInfo(false)} />
          <div className="popup">
            <h3>Chat Controls</h3>
            <ul>
              <li><strong>Speak:</strong> Write your message by voice</li>
              <li><strong>Send:</strong> Send your message</li>
              <li><strong>Feedback:</strong> Go to feedback page</li>
              <li><strong>Info:</strong> Show chat objectives</li>
              <li><strong>Mute:</strong> Toggle bot voice</li>
              <li><strong>Title:</strong> Back to lobby</li>
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
              {scenario.id === 1 ? (
                <>
                  <li><strong>Title:</strong> Microsoft Copilot Satisfaction Check</li>
                  <li><strong>• Your role:</strong> You are a Copilot Welcome Ambassador<br /><strong>• Case History:</strong> You have been in touch with Rachel via email, and she agreed to a short call<p/><strong>• Your goals:</strong><br />• Have a product led growth conversation with Rachel<br />• Gather Copilot product insights</li>
                </>
              ) : scenario.id === 2 ? (
                <>
                  <li><strong>Title:</strong> Microsoft 365 Copilot Chat Adoption Outreach</li>
                  <li>
                    <strong>• Your role:</strong> You are a Copilot Chat Ambassador<br />
                    <strong>• Case History:</strong> You contacted Jordan Evans by email and they agreed to a short call<br />
                    <p/>
                    <strong>• Your goals:</strong><br />
                    • Raise awareness about Microsoft 365 Copilot Chat<br />
                    • Clarify any doubts about licensing, security, or usability<br />
                    • Spark interest in trying Copilot Chat through relevant use cases
                  </li>

                </>
              ) : null}
            </ul>
            <button onClick={() => setShowInfo(false)} className="popup-close-button">
              Close
            </button>
          </div>
        </>
      )}
      {showConfirmDialog && (
        <>
          <div className="popup-overlay" onClick={() => setShowConfirmDialog(false)} />
          <div className="popup">
            <h3>Confirm Navigation</h3>
            <p>Are you sure you want to return to the lobby? Any unsaved progress will be lost.</p>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginTop: '20px' }}>
              <button onClick={() => setShowConfirmDialog(false)} className="popup-close-button">
                Cancel
              </button>
              <button onClick={handleConfirmNavigation} className="popup-close-button" style={{ backgroundColor: 'rgba(255, 0, 0, 0.6)' }}>
                Return to Lobby
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}