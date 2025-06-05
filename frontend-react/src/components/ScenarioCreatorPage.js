import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './ScenarioCreatorPage.css';
import logo from '../GIG+.png';

export default function ScenarioCreatorPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: '',
    description: '',
    personality: '',
    goals: ''
  });

  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Aquí podrías guardar el escenario o navegar
    navigate('/builder');
  };

  return (
    <div className="creator-background">
      <div className="creator-container">
        <div className="creator-header">
          <img src={logo} alt="GigPlus logo" className="creator-logo" />
          <h1>New Scenario</h1>
          <button 
            className="back-button"
            onClick={() => navigate('/')}
          >
            Back to Home
          </button>
        </div>
        <form className="creator-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name">Scenario Name</label>
            <input
              type="text"
              id="name"
              name="name"
              value={form.name}
              onChange={handleChange}
              placeholder="Scenario Name"
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="description">Customer Description</label>
            <textarea
              id="description"
              name="description"
              value={form.description}
              onChange={handleChange}
              placeholder="Customer"
              rows={3}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="personality">Customer Personality</label>
            <textarea
              id="personality"
              name="personality"
              value={form.personality}
              onChange={handleChange}
              placeholder="Customer"
              rows={3}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="goals">Scenario Goals</label>
            <textarea
              id="goals"
              name="goals"
              value={form.goals}
              onChange={handleChange}
              placeholder="Customer"
              rows={3}
              required
            />
          </div>
          <button type="submit" className="conversation-builder-btn">
            Go to Conversation Builder &nbsp; <span style={{fontWeight: 'bold', fontSize: '1.2em'}}>&rarr;</span>
          </button>
        </form>
      </div>
    </div>
  );
} 