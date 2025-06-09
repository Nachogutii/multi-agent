import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './ScenarioCreator.css';

export default function ScenarioSelector() {
  const [scenarios, setScenarios] = useState([]);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetch('http://localhost:8000/api/scenarios')
      .then(res => res.json())
      .then(data => {
        setScenarios(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const filtered = scenarios.filter(s =>
    s.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div style={{
      display: 'flex',
      height: '80vh',
      background: '#040121',
      borderRadius: 16,
      boxShadow: '0 8px 6px rgba(0,0,0,0.1)',
      overflow: 'hidden',
      fontFamily: 'Inter, sans-serif',
      color: '#E6EDF3',
      margin: '2rem auto',
      maxWidth: 900
    }}>
      {/* Left: Scenario List */}
      <div style={{
        width: 340,
        background: 'rgba(115, 114, 133, 0.392)',
        padding: '2rem 1rem',
        display: 'flex',
        flexDirection: 'column',
        borderRight: '1px solid #ffffff17'
      }}>
        <h2 style={{ color: '#E6EDF3', fontWeight: 700, fontSize: 22, marginBottom: 16, textAlign: 'center', fontStyle: 'italic', letterSpacing: 1 }}>SCENARIOS</h2>
        <input
          className="scenario-input"
          type="text"
          placeholder="Search..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ marginBottom: 18 }}
        />
        <div style={{ flex: 1, overflowY: 'auto', borderRadius: 8, background: 'rgba(115, 114, 133, 0.12)' }}>
          {loading ? (
            <div style={{ textAlign: 'center', marginTop: 40 }}>Loading...</div>
          ) : filtered.length === 0 ? (
            <div style={{ textAlign: 'center', marginTop: 40 }}>No scenarios found</div>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              {filtered.map(s => (
                <li
                  key={s.id}
                  onClick={() => setSelected(s)}
                  style={{
                    padding: '0.8rem 1rem',
                    margin: '0.2rem 0',
                    borderRadius: 8,
                    background: selected && selected.id === s.id ? '#281e70' : 'transparent',
                    color: selected && selected.id === s.id ? '#fff' : '#E6EDF3',
                    cursor: 'pointer',
                    fontWeight: selected && selected.id === s.id ? 700 : 400,
                    transition: 'background 0.2s, color 0.2s'
                  }}
                >
                  {s.name}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Right: Details and Create Button */}
      <div style={{
        flex: 1,
        background: '#040121',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '2rem 2.5rem',
        position: 'relative'
      }}>
        {selected ? (
          <div style={{
            width: '100%',
            maxWidth: 400,
            background: 'rgba(115, 114, 133, 0.18)',
            borderRadius: 12,
            padding: '2rem 1.5rem',
            marginBottom: 32,
            boxShadow: '0 2px 8px rgba(40,30,112,0.08)'
          }}>
            <h3 style={{ color: '#E6EDF3', fontWeight: 600, fontSize: 20, marginBottom: 10 }}>{selected.name}</h3>
            <div style={{ color: '#C9D1D9', marginBottom: 10 }}><b>ID:</b> {selected.id}</div>
            <div style={{ color: '#C9D1D9', marginBottom: 10 }}><b>System Prompt:</b> {selected.system_prompt || <i>No prompt</i>}</div>
            <button
              className="start-button"
              style={{ width: '100%', marginTop: 18 }}
              onClick={() => {
                localStorage.setItem('scenarioId', selected.id);
                navigate('/load');
              }}
            >
              Start Scenario
            </button>
          </div>
        ) : (
          <div style={{ color: '#C9D1D9', marginBottom: 32, fontSize: 18, textAlign: 'center' }}>
            Select a scenario to see details and start
          </div>
        )}
        <button
          className="start-button creator-button"
          style={{
            width: 320,
            fontSize: 18,
            padding: '1.2rem',
            marginTop: 12,
            background: '#281e70',
            color: '#fff',
            border: 'none',
            borderRadius: 10,
            fontWeight: 600,
            letterSpacing: 1
          }}
          onClick={() => navigate('/create-scenario')}
        >
          + Create New Scenario
        </button>
      </div>
    </div>
  );
} 