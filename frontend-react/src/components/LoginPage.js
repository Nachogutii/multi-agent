// src/components/LoginPage.js
import React, { useState } from 'react'
import { supabase } from '../lib/supabaseClient'
import './LoginPage.css' // ✅ Estilos propios

export default function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('')
  const [vAccount, setVAccount] = useState('')
  const [sent, setSent] = useState(false)
  const [error, setError] = useState(null)

  const handleLogin = async (e) => {
    e.preventDefault()
    const { error } = await supabase.auth.signInWithOtp({ email })
    if (error) setError(error.message)
    else setSent(true)

    console.log('V-Account:', vAccount) // Puedes usarlo como necesites
  }

  return (
    <div className="login-container">
      <h2>Login to GigPlus Simulator</h2>

      {!sent ? (
        <form onSubmit={handleLogin} className="login-form">
          <input
            type="email"
            className="login-input"
            placeholder="Your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            type="text"
            className="login-input"
            placeholder="Your V-Account"
            value={vAccount}
            onChange={(e) => setVAccount(e.target.value)}
            required
          />
          <button type="submit" className="login-button">
            Send e-mail
          </button>
          {error && <p className="login-error">{error}</p>}
        </form>
      ) : (
        <p className="login-message">✅ Check your inbox for the login link!</p>
      )}
    </div>
  )
}