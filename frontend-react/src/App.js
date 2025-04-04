
import React, { useEffect, useState } from 'react'
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import HomePage from "./components/HomePage";
import ChatPage from "./components/ChatPage";
import FeedbackPage from "./components/FeedbackPage";
import LoginPage from "./components/LoginPage";
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
        <Route path="feedback" element={<FeedbackPage />} />
        <Route path="/chat" element={<ChatPage />} />
      </Routes>
    </Router>
  );
}

export default App;
