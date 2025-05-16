import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './components/HomePage';
import ChatPage from './components/ChatPage';
import FeedbackPage from './components/FeedbackPage';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/feedback" element={<FeedbackPage />} />
      </Routes>
    </Router>
  );
}

export default App;
