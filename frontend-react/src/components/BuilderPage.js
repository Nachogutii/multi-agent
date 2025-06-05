import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './BuilderPage.css';

function PhaseEditModal({ phase, open, onClose, onSave }) {
  const [success, setSuccess] = useState(phase?.success || []);
  const [failure, setFailure] = useState(phase?.failure || []);
  const [conditions, setConditions] = useState(phase?.conditions || []);

  React.useEffect(() => {
    setSuccess(phase?.success || []);
    setFailure(phase?.failure || []);
    setConditions(phase?.conditions || []);
  }, [phase]);

  if (!open || !phase) return null;

  // Handlers for success
  const handleSuccessChange = (idx, value) => {
    setSuccess(success.map((s, i) => i === idx ? value : s));
  };
  const handleAddSuccess = () => setSuccess([...success, '']);
  const handleRemoveSuccess = (idx) => setSuccess(success.filter((_, i) => i !== idx));

  // Handlers for failure
  const handleFailureChange = (idx, value) => {
    setFailure(failure.map((f, i) => i === idx ? value : f));
  };
  const handleAddFailure = () => setFailure([...failure, '']);
  const handleRemoveFailure = (idx) => setFailure(failure.filter((_, i) => i !== idx));

  // Handlers for conditions
  const handleConditionChange = (idx, value) => {
    setConditions(conditions.map((c, i) => i === idx ? value : c));
  };
  const handleAddCondition = () => setConditions([...conditions, '']);
  const handleRemoveCondition = (idx) => setConditions(conditions.filter((_, i) => i !== idx));

  const handleSave = () => {
    onSave({ ...phase, success, failure, conditions });
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-content phase-modal">
        <h3>Conversation Phase: {phase.name}</h3>
        <div className="section">
          <div className="section-label success-label">On Success goes to:</div>
          {success.map((s, idx) => (
            <div className="phase-list-row" key={idx}>
              <input value={s} onChange={e => handleSuccessChange(idx, e.target.value)} />
              <button className="icon-btn" onClick={() => handleRemoveSuccess(idx)} title="Delete">🗑️</button>
            </div>
          ))}
          <button className="icon-btn add-btn" onClick={handleAddSuccess}>＋</button>
        </div>
        <div className="section">
          <div className="section-label failure-label">On Failure goes to:</div>
          {failure.map((f, idx) => (
            <div className="phase-list-row" key={idx}>
              <input value={f} onChange={e => handleFailureChange(idx, e.target.value)} />
              <button className="icon-btn" onClick={() => handleRemoveFailure(idx)} title="Delete">🗑️</button>
            </div>
          ))}
          <button className="icon-btn add-btn" onClick={handleAddFailure}>＋</button>
        </div>
        <div className="section">
          <div className="section-label">Conditions</div>
          {conditions.map((c, idx) => (
            <div className="phase-list-row" key={idx}>
              <input value={c} onChange={e => handleConditionChange(idx, e.target.value)} />
              <button className="examples-btn">Examples</button>
              <button className="icon-btn" onClick={() => handleRemoveCondition(idx)} title="Delete">🗑️</button>
            </div>
          ))}
          <button className="icon-btn add-btn" onClick={handleAddCondition}>＋</button>
        </div>
        <div className="modal-actions">
          <button onClick={handleSave}>Save</button>
          <button onClick={onClose}>Cancel</button>
        </div>
      </div>
    </div>
  );
}

export default function BuilderPage() {
  const [phases, setPhases] = useState([
    { name: 'Welcome', icon: '🏁', success: ['Business Goals', 'PLG Conversation'], failure: ['Abrupt Closure'], conditions: [
      'User introduces himself/herself by Name',
      'User shows interest in what the customer does'
    ] },
    { name: 'Business Goals', icon: '' }
  ]);
  const [editIdx, setEditIdx] = useState(null);
  const navigate = useNavigate();

  const addPhase = () => {
    setPhases([...phases, { name: 'New Phase', icon: '', success: [], failure: [], conditions: [] }]);
  };

  const handleNameChange = (idx, value) => {
    setPhases(phases.map((p, i) => i === idx ? { ...p, name: value } : p));
  };

  const handleEdit = (idx) => setEditIdx(idx);
  const handleCloseModal = () => setEditIdx(null);
  const handleSaveModal = (updatedPhase) => {
    setPhases(phases.map((p, i) => i === editIdx ? updatedPhase : p));
    setEditIdx(null);
  };

  const handleGoToScenario = () => {
    localStorage.setItem('scenarioSummary', JSON.stringify(phases));
    navigate('/scenario-summary');
  };

  return (
    <div className="builder-background">
      <div className="builder-container">
        <h2 className="builder-title">New Scenario &gt; Conversation Phases</h2>
        <div className="phases-list">
          {phases.map((phase, idx) => (
            <div className="phase-card" key={idx}>
              <input className="phase-name-input" value={phase.name} onChange={e => handleNameChange(idx, e.target.value)} />
              {phase.icon && <span className="phase-icon">{phase.icon}</span>}
              <span className="phase-edit" onClick={() => handleEdit(idx)}>✏️</span>
            </div>
          ))}
        </div>
        <button className="add-phase-btn" onClick={addPhase}>
          Add a phase
        </button>
        <button className="go-to-conversation-btn" onClick={handleGoToScenario}>Go to conversation</button>
        {editIdx !== null && phases[editIdx] && (
          <PhaseEditModal
            phase={phases[editIdx]}
            open={editIdx !== null}
            onClose={handleCloseModal}
            onSave={handleSaveModal}
          />
        )}
      </div>
    </div>
  );
} 