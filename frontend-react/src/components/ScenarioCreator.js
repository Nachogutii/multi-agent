import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './ScenarioCreator.css';

function SummaryModal({ isOpen, onClose, onConfirm, scenarioData }) {
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

    return (
        <div className="modal-overlay">
            <div className="modal-content">
                <div className="modal-header">
                    <h2>Scenario Summary</h2>
                </div>
                <div className="modal-body">
                    <div className="modal-section">
                        <h3>General Information</h3>
                        <p><strong>Name:</strong> {scenarioData.scenario.name}</p>
                        <p><strong>System Prompt:</strong> {scenarioData.scenario.system_prompt}</p>
                    </div>

                    <div className="modal-section">
                        <h3>Conditions ({scenarioData.conditions.length})</h3>
                        {scenarioData.conditions.map(c => (
                            <p key={c.id}><strong>[{c.id}]</strong> {c.description}</p>
                        ))}
                    </div>

                    <div className="modal-section">
                        <h3>Phases ({scenarioData.phases.length})</h3>
                        {scenarioData.phases.map(p => (
                            <div key={p.id} className="modal-section" style={{backgroundColor: 'rgba(115, 114, 133, 0.2)'}}>
                                <p><strong>[{p.id}] {p.name}</strong></p>
                                <p><strong>System Prompt:</strong> {p.system_prompt}</p>
                                <p>
                                    <strong>Success Phases:</strong> {displayArray(p.success_phases)}
                                </p>
                                <p>
                                    <strong>Failure Phases:</strong> {displayArray(p.failure_phases)}
                                </p>
                                <p>
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
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [scenarioData, setScenarioData] = useState(null);
    const [scenario, setScenario] = useState({
        name: '',
        system_prompt: ''
    });
    const [conditions, setConditions] = useState([]);
    const [phases, setPhases] = useState([]);

    const addCondition = () => {
        const newId = conditions.length + 1;
        setConditions([...conditions, { id: newId, description: '' }]);
    };

    const updateCondition = (index, description) => {
        const newConditions = [...conditions];
        newConditions[index] = { ...newConditions[index], description };
        setConditions(newConditions);
    };

    const removeCondition = (index) => {
        setConditions(conditions.filter((_, i) => i !== index));
        // Update IDs
        setConditions(prev => prev.map((cond, i) => ({ ...cond, id: i + 1 })));
    };

    const addPhase = () => {
        const newId = phases.length + 1;
        const newPhase = {
            id: newId,
            name: '',
            system_prompt: '',
            success_phases: [],
            failure_phases: [],
            conditions: []
        };
        setPhases([...phases, newPhase]);
    };

    const updatePhase = (index, field, value) => {
        const newPhases = [...phases];
        newPhases[index] = { ...newPhases[index], [field]: value };
        setPhases(newPhases);
    };

    const addPhaseId = (phaseIndex, field, id) => {
        if (!/^\d+$/.test(id)) return; // Validar que sea un número
        
        const newPhases = [...phases];
        const currentPhase = { ...newPhases[phaseIndex] };
        const idNumber = parseInt(id);
        
        if (!currentPhase[field].includes(idNumber)) {
            currentPhase[field] = [...currentPhase[field], idNumber];
            newPhases[phaseIndex] = currentPhase;
            setPhases(newPhases);
        }
    };

    const removePhaseId = (phaseIndex, field, id) => {
        const newPhases = [...phases];
        const currentPhase = { ...newPhases[phaseIndex] };
        currentPhase[field] = currentPhase[field].filter(existingId => existingId !== id);
        newPhases[phaseIndex] = currentPhase;
        setPhases(newPhases);
    };

    const removePhase = (index) => {
        setPhases(phases.filter((_, i) => i !== index));
        // Update IDs
        setPhases(prev => prev.map((phase, i) => ({ ...phase, id: i + 1 })));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        try {
            // Preparar los datos según el schema
            const data = {
                scenario: {
                    name: scenario.name,
                    system_prompt: scenario.system_prompt
                },
                conditions: conditions.map(condition => ({
                    id: condition.id,
                    description: condition.description
                })),
                phases: phases.map(phase => ({
                    id: phase.id,
                    name: phase.name,
                    system_prompt: phase.system_prompt,
                    success_phases: phase.success_phases || [],
                    failure_phases: phase.failure_phases || []
                })),
                phase_conditions: phases.flatMap(phase => 
                    (phase.conditions || []).map(conditionId => ({
                        phase_id: phase.id,
                        conditions_id: Number(conditionId)
                    }))
                )
            };

            // Verificar que los arrays no son undefined
            data.phases.forEach(phase => {
                if (!Array.isArray(phase.success_phases)) phase.success_phases = [];
                if (!Array.isArray(phase.failure_phases)) phase.failure_phases = [];
            });

            console.log('Datos preparados:', JSON.stringify(data, null, 2));
            setScenarioData(data);
            setIsModalOpen(true);
        } catch (error) {
            console.error('Error preparing data:', error);
            alert('Error preparing scenario data: ' + error.message);
        }
    };

    const handleConfirm = async () => {
        try {
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
                throw new Error(responseData.detail || 'Error creating scenario');
            }

            alert(`Scenario successfully created with ID: ${responseData.scenario_id}`);
            navigate('/');
        } catch (error) {
            console.error('Complete error:', error);
            alert('Error: ' + (error.message || 'Unknown error creating scenario'));
        } finally {
            setIsModalOpen(false);
        }
    };

    return (
        <div className="scenario-creator">
            <h1>Create New Scenario</h1>
            
            <form onSubmit={handleSubmit}>
                <div className="section">
                    <h2>Scenario Information</h2>
                    <input
                        type="text"
                        placeholder="Scenario name"
                        value={scenario.name}
                        onChange={(e) => setScenario({...scenario, name: e.target.value})}
                        required
                    />
                    <textarea
                        placeholder="System prompt"
                        value={scenario.system_prompt}
                        onChange={(e) => setScenario({...scenario, system_prompt: e.target.value})}
                        required
                    />
                </div>

                <div className="section">
                    <h2>Conditions</h2>
                    <button type="button" onClick={addCondition}>Add Condition</button>
                    {conditions.map((condition, index) => (
                        <div key={index} className="condition-item">
                            <span>ID: {condition.id}</span>
                            <input
                                type="text"
                                placeholder="Condition description"
                                value={condition.description}
                                onChange={(e) => updateCondition(index, e.target.value)}
                                required
                            />
                            <button type="button" onClick={() => removeCondition(index)}>Remove</button>
                        </div>
                    ))}
                </div>

                <div className="section">
                    <h2>Phases</h2>
                    <button type="button" onClick={addPhase}>Add Phase</button>
                    {phases.map((phase, index) => (
                        <div key={index} className="phase-item">
                            <span>ID: {phase.id}</span>
                            <input
                                type="text"
                                placeholder="Phase name"
                                value={phase.name}
                                onChange={(e) => updatePhase(index, 'name', e.target.value)}
                                required
                            />
                            <textarea
                                placeholder="Phase system prompt"
                                value={phase.system_prompt}
                                onChange={(e) => updatePhase(index, 'system_prompt', e.target.value)}
                                required
                            />
                            
                            <div className="array-input-container">
                                <label>Success phase IDs:</label>
                                <div className="id-input-group">
                                    <input
                                        type="number"
                                        placeholder="Add ID"
                                        onKeyPress={(e) => {
                                            if (e.key === 'Enter') {
                                                e.preventDefault();
                                                addPhaseId(index, 'success_phases', e.target.value);
                                                e.target.value = '';
                                            }
                                        }}
                                    />
                                    <div className="id-tags">
                                        {phase.success_phases.map((id) => (
                                            <span key={id} className="id-tag">
                                                {id}
                                                <button 
                                                    type="button" 
                                                    className="remove-id"
                                                    onClick={() => removePhaseId(index, 'success_phases', id)}
                                                >
                                                    ×
                                                </button>
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            <div className="array-input-container">
                                <label>Failure phase IDs:</label>
                                <div className="id-input-group">
                                    <input
                                        type="number"
                                        placeholder="Add ID"
                                        onKeyPress={(e) => {
                                            if (e.key === 'Enter') {
                                                e.preventDefault();
                                                addPhaseId(index, 'failure_phases', e.target.value);
                                                e.target.value = '';
                                            }
                                        }}
                                    />
                                    <div className="id-tags">
                                        {phase.failure_phases.map((id) => (
                                            <span key={id} className="id-tag">
                                                {id}
                                                <button 
                                                    type="button" 
                                                    className="remove-id"
                                                    onClick={() => removePhaseId(index, 'failure_phases', id)}
                                                >
                                                    ×
                                                </button>
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            <div className="array-input-container">
                                <label>Condition IDs:</label>
                                <div className="id-input-group">
                                    <input
                                        type="number"
                                        placeholder="Add ID"
                                        onKeyPress={(e) => {
                                            if (e.key === 'Enter') {
                                                e.preventDefault();
                                                addPhaseId(index, 'conditions', e.target.value);
                                                e.target.value = '';
                                            }
                                        }}
                                    />
                                    <div className="id-tags">
                                        {phase.conditions.map((id) => (
                                            <span key={id} className="id-tag">
                                                {id}
                                                <button 
                                                    type="button" 
                                                    className="remove-id"
                                                    onClick={() => removePhaseId(index, 'conditions', id)}
                                                >
                                                    ×
                                                </button>
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            <button type="button" onClick={() => removePhase(index)}>Remove Phase</button>
                        </div>
                    ))}
                </div>

                <button type="submit" className="submit-button">Create Scenario</button>
            </form>

            <SummaryModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onConfirm={handleConfirm}
                scenarioData={scenarioData}
            />
        </div>
    );
} 