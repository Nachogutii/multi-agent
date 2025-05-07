import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import * as SpeechSDK from "microsoft-cognitiveservices-speech-sdk";
import './ChatPage.css';

const HARDCODED_SEQUENCE = [
  "Thanks, yeah—it was handled really well.",
  "Honestly, I like the flexibility it gives our team, especially with remote work. But I still find Teams and OneDrive a bit clunky when it comes to managing access. Like, I'm never 100% sure who can see what, and I worry about sensitive files being shared too broadly.",
  "No worries, I'm glad the feedback is helpful.",
  "Yeah, I use ChatGPT here and there—mostly for writing drafts or brainstorming ideas. I'm not super technical, but I like seeing what it can do.",
  "Oh? I didn't know that. Is it like ChatGPT?",
  "That last one would be a game-changer. I didn't realize it could help with that kind of thing.",
  "Yeah, that'd be great."  
];

const speechKey = process.env.REACT_APP_SPEECH_KEY;
const speechRegion = process.env.REACT_APP_SPEECH_REGION;

export default function CopilotChatScenario() {
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [showInfo, setShowInfo] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [hardcodedStep, setHardcodedStep] = useState(0);
  const messagesEndRef = useRef(null);
  const synthesizerRef = useRef(null);
  const navigate = useNavigate();

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
        console.log("Bot muted manually.");
      }, (err) => {
        console.error("Error stopping voice:", err);
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

    let response;
    if (hardcodedStep < HARDCODED_SEQUENCE.length) {
      response = HARDCODED_SEQUENCE[hardcodedStep];
      setHardcodedStep(hardcodedStep + 1);
    } else {
      response = HARDCODED_SEQUENCE[HARDCODED_SEQUENCE.length - 1];
    }

    setUserInput("");
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: response }
      ]);
      speakResponse(response);
      setLoading(false);
    }, 1500);
  };

  const handleFeedbackClick = () => {
    navigate("/feedback-chat");
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="chat-header-left">
          <h3 className="scenario-title">Copilot Chat</h3>
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
          className={`voice-button${listening ? ' listening' : ''}`}
          disabled={loading || listening}
          onClick={recognizeSpeech}
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

      {showInfo && (
        <>
          <div className="popup-overlay" onClick={() => setShowInfo(false)} />
          <div className="popup">
            <h3>sinem arslan maquinota</h3>
            <button onClick={() => setShowInfo(false)} className="popup-close-button">
              Close
            </button>
          </div>
        </>
      )}
    </div>
  );
} 