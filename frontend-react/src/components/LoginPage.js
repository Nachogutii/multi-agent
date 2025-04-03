// src/components/LoginPage.js
import React, { useState } from 'react'
import { supabase } from '../lib/supabaseClient'

export default function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [error, setError] = useState(null)

  const handleLogin = async (e) => {
    e.preventDefault()
    const { error } = await supabase.auth.signInWithOtp({ email })
    if (error) setError(error.message)
    else setSent(true)
  }

  return (
    <div className="login-page">
      <h2>Login</h2>
      {!sent ? (
        <form onSubmit={handleLogin}>
          <input
            type="email"
            placeholder="Your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <button type="submit">Send Magic Link</button>
          {error && <p style={{ color: 'red' }}>{error}</p>}
        </form>
      ) : (
        <p>✅ Check your inbox for the login link!</p>
      )}
    </div>
  )
}
