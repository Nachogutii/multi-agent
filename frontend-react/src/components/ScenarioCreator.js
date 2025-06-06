import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './ScenarioCreator.css';

export default function ScenarioCreator() {
    const navigate = useNavigate();
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
            success_phases: [],  // Array normal para manejar IDs individuales
            failure_phases: [],  // Array normal para manejar IDs individuales
            conditions: []  // Array de condition IDs
        };
        console.log('Adding new phase:', newPhase);
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
        
        // Preparar los datos según el schema
        const scenarioData = {
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
                success_phases: phase.success_phases,  // Ya es un array
                failure_phases: phase.failure_phases   // Ya es un array
            })),
            phase_conditions: phases.flatMap(phase => 
                phase.conditions.map(conditionId => ({
                    phase_id: phase.id,
                    conditions_id: conditionId
                }))
            )
        };

        console.log('JSON generado:', JSON.stringify(scenarioData, null, 2));

        // Mostrar resumen
        const summary = `
=== RESUMEN DEL ESCENARIO ===

Nombre: ${scenarioData.scenario.name}
System Prompt: ${scenarioData.scenario.system_prompt}

=== CONDICIONES (${scenarioData.conditions.length}) ===
${scenarioData.conditions.map(c => `[${c.id}] ${c.description}`).join('\n')}

=== FASES (${scenarioData.phases.length}) ===
${scenarioData.phases.map(p => `
[${p.id}] ${p.name}
  - System Prompt: ${p.system_prompt}
  - Success Phases: [${p.success_phases.join(',')}]
  - Failure Phases: [${p.failure_phases.join(',')}]
  - Conditions: ${scenarioData.phase_conditions
    .filter(pc => pc.phase_id === p.id)
    .map(pc => pc.conditions_id)
    .join(', ')}`).join('\n')}
`;

        const confirmed = window.confirm(
            `Por favor, revisa el resumen del escenario:\n\n${summary}\n\n¿Deseas proceder con la creación?`
        );

        if (confirmed) {
            try {
                const response = await fetch('http://localhost:8000/api/scenarios', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(scenarioData)
                });

                if (response.ok) {
                    const result = await response.json();
                    console.log('Respuesta del servidor:', result);
                    alert(`Escenario creado exitosamente con ID: ${result.scenario_id}`);
                    navigate('/');  // Ahora sí navegamos ya que se creó en la base de datos
                } else {
                    const error = await response.json();
                    alert('Error: ' + (error.detail || 'Error desconocido'));
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
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
                                        placeholder="Agregar ID"
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
                                        placeholder="Agregar ID"
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
                                        placeholder="Agregar ID"
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
        </div>
    );
} 