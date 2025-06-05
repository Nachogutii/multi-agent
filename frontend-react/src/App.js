import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './components/HomePage';
import ChatPage from './components/ChatPage';
import FeedbackPage from './components/FeedbackPage';
import LoginPage from "./components/LoginPage";
import LoadPage from './components/LoadPage';
import ScenarioCreatorPage from './components/ScenarioCreatorPage';
import BuilderPage from './components/BuilderPage';
import ScenarioSummaryPage from './components/ScenarioSummaryPage';
import { supabase } from "./lib/supabaseClient";

function App() {
  const [user, setUser] = useState(null)

  useEffect(() => {
    supabase.auth.getUser().then(({ data: { user } }) => setUser(user))
    supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user || null)
    })
  }, [])

  if (!user) return <LoginPage />
  
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/load" element={<LoadPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/feedback" element={<FeedbackPage />} />
        <Route path="/scenario-creator" element={<ScenarioCreatorPage />} />
        <Route path="/builder" element={<BuilderPage />} />
        <Route path="/scenario-summary" element={<ScenarioSummaryPage />} />
      </Routes>
    </Router>
  );
}

export default App;
