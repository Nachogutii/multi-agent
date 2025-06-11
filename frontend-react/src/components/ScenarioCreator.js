import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './ScenarioCreator.css';

function ScenarioSummaryModal({ isOpen, onClose, onConfirm, scenarioData, error }) {
    if (!isOpen || !scenarioData) return null;

    // Helper function to display arrays
    const displayArray = (arr) => {
        if (!arr || !Array.isArray(arr)) return '[]';
        return `[${arr.join(', ')}]`;
    };

    // Function to get phase conditions
    const getPhaseConditions = (phaseId) => {
        const conditions = scenarioData.phase_conditions
            .filter(pc => pc.phase_id === phaseId)
            .map(pc => pc.conditions_id);
        return displayArray(conditions);
    };

    // Function to highlight the section with error
    const getErrorHighlight = (sectionText) => {
        if (!error) return {};
        const errorLower = error.toLowerCase();
        const sectionLower = sectionText.toLowerCase();
        
        if (errorLower.includes(sectionLower)) {
            return {
                backgroundColor: 'rgba(255, 0, 0, 0.1)',
                border: '1px solid rgba(255, 0, 0, 0.3)',
                padding: '0.5rem',
                borderRadius: '4px'
            };
        }
        return {};
    };

    return (
        <div className="modal-overlay">
            <div className="modal-content">
                <div className="modal-header">
                    <h2>Scenario Summary</h2>
                </div>
                <div className="modal-body">
                    {error && (
                        <div className="error-message">
                            {error}
                        </div>
                    )}
                    <div className="modal-section" style={getErrorHighlight('scenario')}>
                        <h3>General Information</h3>
                        <p><strong>Name:</strong> {scenarioData.scenario.name}</p>
                        <p><strong>System Prompt:</strong> {scenarioData.scenario.system_prompt}</p>
                    </div>

                    <div className="modal-section" style={getErrorHighlight('condition')}>
                        <h3>Conditions ({scenarioData.conditions.length})</h3>
                        {scenarioData.conditions.map(c => (
                            <p key={c.id} style={getErrorHighlight(c.description)}><strong>[{c.id}]</strong> {c.description}</p>
                        ))}
                    </div>

                    <div className="modal-section" style={getErrorHighlight('phase')}>
                        <h3>Phases ({scenarioData.phases.length})</h3>
                        {scenarioData.phases.map(p => (
                            <div key={p.id} className="modal-section" style={{
                                ...getErrorHighlight(p.name),
                                backgroundColor: 'rgba(115, 114, 133, 0.2)'
                            }}>
                                <p><strong>[{p.id}] {p.name}</strong></p>
                                <p><strong>System Prompt:</strong> {p.system_prompt}</p>
                                <p style={getErrorHighlight('success phase')}>
                                    <strong>Success Phases:</strong> {displayArray(p.success_phases)}
                                </p>
                                <p style={getErrorHighlight('failure phase')}>
                                    <strong>Failure Phases:</strong> {displayArray(p.failure_phases)}
                                </p>
                                <p style={getErrorHighlight('condition')}>
                                    <strong>Conditions:</strong> {getPhaseConditions(p.id)}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
                <div className="modal-footer">
                    <button className="modal-button cancel" onClick={onClose}>
                        Cancel
                    </button>
                    <button className="modal-button confirm" onClick={onConfirm}>
                        Confirm and Create
                    </button>
                </div>
            </div>
        </div>
    );
}

export default function ScenarioCreator() {
    const navigate = useNavigate();
    const [isSummaryModalOpen, setIsSummaryModalOpen] = useState(false);
    const [scenarioData, setScenarioData] = useState(null);
    const [error, setError] = useState(null);
    const [scenarioInfo, setScenarioInfo] = useState({
        name: '',
        system_prompt: ''
    });
    const [scenarioConditions, setScenarioConditions] = useState([]);
    const [scenarioPhases, setScenarioPhases] = useState([]);

    const addScenarioCondition = () => {
        const newConditionId = scenarioConditions.length + 1;
        setScenarioConditions([...scenarioConditions, { id: newConditionId, description: '' }]);
    };

    const updateScenarioCondition = (index, description) => {
        const newConditions = [...scenarioConditions];
        newConditions[index] = { ...newConditions[index], description };
        setScenarioConditions(newConditions);
    };

    const removeScenarioCondition = (index) => {
        setScenarioConditions(scenarioConditions.filter((_, i) => i !== index));
        // Update IDs
        setScenarioConditions(prev => prev.map((cond, i) => ({ ...cond, id: i + 1 })));
    };

    const addScenarioPhase = () => {
        const newPhaseId = scenarioPhases.length + 1;
        const newPhase = {
            id: newPhaseId,
            name: '',
            system_prompt: '',
            success_phases: [],
            failure_phases: [],
            conditions: []
        };
        setScenarioPhases([...scenarioPhases, newPhase]);
    };

    const updateScenarioPhase = (index, field, value) => {
        const newPhases = [...scenarioPhases];
        newPhases[index] = { ...newPhases[index], [field]: value };
        setScenarioPhases(newPhases);
    };

    const addScenarioPhaseTransition = (phaseIndex, field, id) => {
        if (!/^\d+$/.test(id)) return;
        
        const newPhases = [...scenarioPhases];
        const currentPhase = { ...newPhases[phaseIndex] };
        const idNumber = parseInt(id);
        
        if (!currentPhase[field].includes(idNumber)) {
            currentPhase[field] = [...currentPhase[field], idNumber];
            newPhases[phaseIndex] = currentPhase;
            setScenarioPhases(newPhases);
        }
    };

    const removeScenarioPhaseTransition = (phaseIndex, field, id) => {
        const newPhases = [...scenarioPhases];
        const currentPhase = { ...newPhases[phaseIndex] };
        currentPhase[field] = currentPhase[field].filter(existingId => existingId !== id);
        newPhases[phaseIndex] = currentPhase;
        setScenarioPhases(newPhases);
    };

    const removeScenarioPhase = (index) => {
        setScenarioPhases(scenarioPhases.filter((_, i) => i !== index));
        // Update IDs
        setScenarioPhases(prev => prev.map((phase, i) => ({ ...phase, id: i + 1 })));
    };

    const handleScenarioSubmit = async (e) => {
        e.preventDefault();
        
        try {
            const data = {
                scenario: {
                    name: scenarioInfo.name,
                    system_prompt: scenarioInfo.system_prompt
                },
                conditions: scenarioConditions.map(condition => ({
                    id: condition.id,
                    description: condition.description
                })),
                phases: scenarioPhases.map(phase => ({
                    id: phase.id,
                    name: phase.name,
                    system_prompt: phase.system_prompt,
                    success_phases: phase.success_phases || [],
                    failure_phases: phase.failure_phases || []
                })),
                phase_conditions: scenarioPhases.flatMap(phase => 
                    (phase.conditions || []).map(conditionId => ({
                        phase_id: phase.id,
                        conditions_id: Number(conditionId)
                    }))
                )
            };

            data.phases.forEach(phase => {
                if (!Array.isArray(phase.success_phases)) phase.success_phases = [];
                if (!Array.isArray(phase.failure_phases)) phase.failure_phases = [];
            });

            console.log('Prepared scenario data:', JSON.stringify(data, null, 2));
            setScenarioData(data);
            setIsSummaryModalOpen(true);
        } catch (error) {
            console.error('Error preparing scenario data:', error);
            alert('Error preparing scenario data: ' + error.message);
        }
    };

    const handleScenarioConfirm = async () => {
        try {
            setError(null); // Limpiar error anterior
            if (!scenarioData) {
                throw new Error('No scenario data to send');
            }

            // Asegurarnos de que los datos están correctamente formateados
            const dataToSend = {
                scenario: scenarioData.scenario,
                conditions: scenarioData.conditions,
                phases: scenarioData.phases.map(phase => ({
                    id: phase.id,
                    name: phase.name,
                    system_prompt: phase.system_prompt,
                    success_phases: Array.isArray(phase.success_phases) ? phase.success_phases : [],
                    failure_phases: Array.isArray(phase.failure_phases) ? phase.failure_phases : []
                })),
                phase_conditions: scenarioData.phase_conditions.map(pc => ({
                    phase_id: Number(pc.phase_id),
                    conditions_id: Number(pc.conditions_id)
                }))
            };

            console.log('Enviando datos al servidor:', JSON.stringify(dataToSend, null, 2));
            
            const response = await fetch('http://localhost:8000/api/scenarios', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(dataToSend)
            });

            const responseData = await response.json();
            console.log('Server response:', responseData);

            if (!response.ok) {
                // Extraer el mensaje de error de la respuesta
                let errorMessage = 'Unknown error creating scenario';
                if (responseData.detail) {
                    if (typeof responseData.detail === 'object') {
                        // Si detail es un objeto, intentamos extraer el mensaje útil
                        if (responseData.detail.msg) {
                            errorMessage = responseData.detail.msg;
                        } else if (Array.isArray(responseData.detail) && responseData.detail[0]?.msg) {
                            errorMessage = responseData.detail[0].msg;
                        }
                    } else {
                        // Si detail es una string, la usamos directamente
                        errorMessage = responseData.detail;
                    }
                }
                throw new Error(errorMessage);
            }

            alert(`Scenario successfully created with ID: ${responseData.scenario_id}`);
            setIsSummaryModalOpen(false);
            navigate('/');
        } catch (error) {
            console.error('Complete error:', error);
            setError(error.message || 'Unknown error creating scenario');
            // No cerramos el modal para mantener la información
        }
    };

    return (
        <div className="scenario-creator-container">
            <h1>Create New Scenario</h1>
            
            <form onSubmit={handleScenarioSubmit}>
                <div className="scenario-info-section">
                    <h2>Scenario Information</h2>
                    <input
                        type="text"
                        placeholder="Scenario name"
                        value={scenarioInfo.name}
                        onChange={(e) => setScenarioInfo({...scenarioInfo, name: e.target.value})}
                        required
                        className="scenario-input"
                    />
                    <textarea
                        placeholder="System prompt"
                        value={scenarioInfo.system_prompt}
                        onChange={(e) => setScenarioInfo({...scenarioInfo, system_prompt: e.target.value})}
                        required
                        className="scenario-textarea"
                    />
                </div>

                <div className="scenario-conditions-section">
                    <h2>Conditions</h2>
                    <button type="button" onClick={addScenarioCondition} className="scenario-add-button">Add Condition</button>
                    {scenarioConditions.map((condition, index) => (
                        <div key={index} className="scenario-condition-item">
                            <span className="scenario-condition-id">ID: {condition.id}</span>
                            <input
                                type="text"
                                placeholder="Condition description"
                                value={condition.description}
                                onChange={(e) => updateScenarioCondition(index, e.target.value)}
                                required
                                className="scenario-input"
                            />
                            <button type="button" onClick={() => removeScenarioCondition(index)} className="scenario-remove-button">Remove</button>
                        </div>
                    ))}
                </div>

                <div className="scenario-phases-section">
                    <h2>Phases</h2>
                    <button type="button" onClick={addScenarioPhase} className="scenario-add-button">Add Phase</button>
                    {scenarioPhases.map((phase, index) => (
                        <div key={index} className="scenario-phase-item">
                            <span className="scenario-phase-id">ID: {phase.id}</span>
                            <input
                                type="text"
                                placeholder="Phase name"
                                value={phase.name}
                                onChange={(e) => updateScenarioPhase(index, 'name', e.target.value)}
                                required
                                className="scenario-input"
                            />
                            <textarea
                                placeholder="Phase system prompt"
                                value={phase.system_prompt}
                                onChange={(e) => updateScenarioPhase(index, 'system_prompt', e.target.value)}
                                required
                                className="scenario-textarea"
                            />
                            
                            <div className="scenario-transitions-container">
                                <label>Success phase IDs:</label>
                                <div className="scenario-transition-group">
                                    <input
                                        type="number"
                                        placeholder="Add ID"
                                        className="scenario-input"
                                        onKeyPress={(e) => {
                                            if (e.key === 'Enter') {
                                                e.preventDefault();
                                                addScenarioPhaseTransition(index, 'success_phases', e.target.value);
                                                e.target.value = '';
                                            }
                                        }}
                                    />
                                    <div className="scenario-transition-tags">
                                        {phase.success_phases.map((id) => (
                                            <span key={id} className="scenario-transition-tag">
                                                {id}
                                                <button 
                                                    type="button" 
                                                    className="scenario-transition-remove"
                                                    onClick={() => removeScenarioPhaseTransition(index, 'success_phases', id)}
                                                >
                                                    ×
                                                </button>
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            <div className="scenario-transitions-container">
                                <label>Failure phase IDs:</label>
                                <div className="scenario-transition-group">
                                    <input
                                        type="number"
                                        placeholder="Add ID"
                                        className="scenario-input"
                                        onKeyPress={(e) => {
                                            if (e.key === 'Enter') {
                                                e.preventDefault();
                                                addScenarioPhaseTransition(index, 'failure_phases', e.target.value);
                                                e.target.value = '';
                                            }
                                        }}
                                    />
                                    <div className="scenario-transition-tags">
                                        {phase.failure_phases.map((id) => (
                                            <span key={id} className="scenario-transition-tag">
                                                {id}
                                                <button 
                                                    type="button" 
                                                    className="scenario-transition-remove"
                                                    onClick={() => removeScenarioPhaseTransition(index, 'failure_phases', id)}
                                                >
                                                    ×
                                                </button>
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            <div className="scenario-transitions-container">
                                <label>Condition IDs:</label>
                                <div className="scenario-transition-group">
                                    <input
                                        type="number"
                                        placeholder="Add ID"
                                        className="scenario-input"
                                        onKeyPress={(e) => {
                                            if (e.key === 'Enter') {
                                                e.preventDefault();
                                                addScenarioPhaseTransition(index, 'conditions', e.target.value);
                                                e.target.value = '';
                                            }
                                        }}
                                    />
                                    <div className="scenario-transition-tags">
                                        {phase.conditions.map((id) => (
                                            <span key={id} className="scenario-transition-tag">
                                                {id}
                                                <button 
                                                    type="button" 
                                                    className="scenario-transition-remove"
                                                    onClick={() => removeScenarioPhaseTransition(index, 'conditions', id)}
                                                >
                                                    ×
                                                </button>
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            <button type="button" onClick={() => removeScenarioPhase(index)} className="scenario-remove-button">Remove Phase</button>
                        </div>
                    ))}
                </div>

                <button type="submit" className="scenario-submit-button">Create Scenario</button>
            </form>

            <ScenarioSummaryModal
                isOpen={isSummaryModalOpen}
                onClose={() => setIsSummaryModalOpen(false)}
                onConfirm={handleScenarioConfirm}
                scenarioData={scenarioData}
                error={error}
            />
        </div>
    );
} 