// src/components/LoginPage.js
import React, { useState } from 'react'
import { supabase } from '../lib/supabaseClient'
import logo from '../GIG+.png'
import background from '../background.png'
import './LoginPage.css'

export default function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('')
  const [vAccount, setVAccount] = useState('')
  const [sent, setSent] = useState(false)
  const [error, setError] = useState(null)

  const handleLogin = async (e) => {
    e.preventDefault()
    const { error } = await supabase.auth.signInWithOtp({ email })
    if (error) setError(error.message)
    else {
      setSent(true)
      localStorage.setItem("v_account", vAccount)
    }
  
    console.log('V-Account:', vAccount)
  }
  

  return (
    <div
      className="login-page-bg"
      style={{
        backgroundImage: `url(${background})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        backgroundAttachment: 'fixed',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem'
      }}
    >
      <div className="login-container">
        <div className="login-title-row">
          <img src={logo} alt="GigPlus logo" className="login-logo-inline" />
          <h2>Login to GigPlus</h2>
        </div>

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
    </div>
  )
}