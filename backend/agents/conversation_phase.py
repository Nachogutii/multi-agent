from enum import Enum
from typing import List, Dict, Optional
import time

class ConversationPhase(Enum):
    INTRODUCTION_DISCOVERY = "introduction_discovery"
    VALUE_PROPOSITION = "value_proposition"
    OBJECTION_HANDLING = "objection_handling"
    CLOSING = "closing"

class ConversationPhaseManager:
    """Manages the progression of PLG conversation phases using AI-based semantic analysis."""
    
    def __init__(self, azure_client=None, deployment=None):
        self.current_phase = ConversationPhase.INTRODUCTION_DISCOVERY
        self.phase_history: List[Dict] = []
        self.client = azure_client
        self.deployment = deployment
        self.conversation_history: List[Dict] = []
        
        # Phase-specific semantic patterns and intents
        self.phase_patterns = {
            ConversationPhase.INTRODUCTION_DISCOVERY: {
                "intents": [
                    "greeting",
                    "introduction",
                    "role_identification",
                    "needs_discovery",
                    "problem_understanding"
                ],
                "key_aspects": [
                    "establishing rapport",
                    "understanding customer context",
                    "identifying customer role",
                    "discovering customer needs",
                    "understanding current situation"
                ]
            },
            ConversationPhase.VALUE_PROPOSITION: {
                "intents": [
                    "feature_presentation",
                    "benefit_explanation",
                    "solution_demonstration",
                    "value_communication",
                    "use_case_sharing"
                ],
                "key_aspects": [
                    "presenting product features",
                    "explaining benefits",
                    "showing value proposition",
                    "demonstrating capabilities",
                    "sharing success stories"
                ]
            },
            ConversationPhase.OBJECTION_HANDLING: {
                "intents": [
                    "concern_acknowledgment",
                    "objection_handling",
                    "clarification",
                    "solution_presentation",
                    "reassurance"
                ],
                "key_aspects": [
                    "addressing concerns",
                    "providing solutions",
                    "clarifying doubts",
                    "handling objections",
                    "building confidence"
                ]
            },
            ConversationPhase.CLOSING: {
                "intents": [
                    "next_steps",
                    "appreciation",
                    "farewell",
                    "follow_up",
                    "commitment"
                ],
                "key_aspects": [
                    "confirming next steps",
                    "expressing gratitude",
                    "saying goodbye",
                    "offering support",
                    "ensuring satisfaction"
                ]
            }
        }
    
    def add_message(self, message: str, is_agent: bool = True):
        """Adds a message to the conversation history and triggers phase analysis."""
        self.conversation_history.append({
            "message": message,
            "is_agent": is_agent,
            "timestamp": time.time()
        })
        
        # Analyze the message immediately without starting monitoring
        new_phase = self._analyze_conversation_semantics()
        if new_phase != self.current_phase:
            self._update_phase(new_phase)
    
    def analyze_message(self, message: str) -> ConversationPhase:
        """Analyzes the conversation to determine the current phase using AI."""
        # Get the current phase based on semantic analysis
        new_phase = self._analyze_conversation_semantics()
        
        # Update phase if changed
        if new_phase != self.current_phase:
            self._update_phase(new_phase)
        
        return new_phase
    
    def _analyze_conversation_semantics(self) -> ConversationPhase:
        """Analyzes the conversation history to determine the current phase using AI."""
        if not self.client or not self.deployment:
            return self.current_phase
            
        # Prepare conversation context for analysis
        conversation_context = self._prepare_conversation_context()
        
        # Create a more sophisticated analysis prompt
        analysis_prompt = f"""
        Analyze this conversation and determine which phase it's currently in.
        Consider the natural flow, context, and intent of the entire conversation.

        Current Phase: {self.current_phase.value}
        Number of Messages: {len(self.conversation_history)}
        Phase History: {[phase['to_phase'].value for phase in self.phase_history]}

        Conversation History:
        {conversation_context}

        Analyze the conversation considering:

        1. Natural Progression:
           - How has the conversation evolved?
           - What topics have been covered?
           - Is there a logical flow between topics?

        2. Context and Intent:
           - What is the current focus of the discussion?
           - Are there any underlying themes or patterns?
           - What is the emotional tone of the conversation?

        3. Relationship Stage:
           - How has the relationship between agent and customer developed?
           - Is there a sense of resolution or completion?
           - Are there signs of mutual understanding?

        4. Conversation Dynamics:
           - Are there signs of conclusion or winding down?
           - Is there a natural break in the conversation?
           - Are there indicators of next steps or future actions?

        5. Phase-Specific Analysis:
           - Has the conversation reached a natural conclusion?
           - Are there signs of satisfaction or resolution?
           - Is there a clear indication of conversation ending?

        Phase Descriptions:
        1. INTRODUCTION_DISCOVERY: Initial contact, rapport building, understanding context
        2. VALUE_PROPOSITION: Presenting benefits, features, and value
        3. OBJECTION_HANDLING: Addressing concerns, providing solutions
        4. CLOSING: Natural conclusion, next steps, mutual understanding

        Important Rules:
        1. Consider the entire conversation context, not just keywords
        2. Look for natural conversation flow and progression
        3. Pay attention to emotional and contextual indicators
        4. Consider the relationship development
        5. Look for signs of natural conclusion or resolution
        6. Only move to CLOSING phase if there are clear signs of conversation ending
        7. Consider the number of messages and current phase when making decisions

        Return only the phase name (e.g., "INTRODUCTION_DISCOVERY").
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": """You are an expert conversation analyst.
                    Your task is to analyze conversations holistically and determine their current phase.
                    Consider the natural flow, context, and relationship development.
                    Look for signs of natural conclusion and resolution.
                    Be conservative about moving to the CLOSING phase - only do so with clear signs of conversation ending.
                    Return only the exact phase name without any additional text."""},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.2,
                max_tokens=50
            )
            
            # Parse the response to get the phase
            phase_name = response.choices[0].message.content.strip()
            print(f"Phase Analysis Result: {phase_name} (Current: {self.current_phase.value})")
            
            # Validate the phase name
            try:
                new_phase = ConversationPhase(phase_name.lower())
                
                # Additional validation to prevent phase regression
                if new_phase != self.current_phase:
                    # Check if the new phase follows logical progression
                    phase_order = {
                        ConversationPhase.INTRODUCTION_DISCOVERY: 0,
                        ConversationPhase.VALUE_PROPOSITION: 1,
                        ConversationPhase.OBJECTION_HANDLING: 2,
                        ConversationPhase.CLOSING: 3
                    }
                    
                    current_order = phase_order.get(self.current_phase, -1)
                    new_order = phase_order.get(new_phase, -1)
                    
                    # Only allow forward progression or staying in the same phase
                    if new_order < current_order:
                        print(f"Invalid phase regression detected: {self.current_phase} -> {new_phase}")
                        return self.current_phase
                    
                    # Additional validation for CLOSING phase
                    if new_phase == ConversationPhase.CLOSING:
                        # Require at least 4 messages before allowing closing phase
                        if len(self.conversation_history) < 4:
                            print("Not enough messages for closing phase")
                            return self.current_phase
                        
                        # Check if we've been through other phases
                        if not any(phase['to_phase'] == ConversationPhase.VALUE_PROPOSITION for phase in self.phase_history):
                            print("Haven't reached value proposition phase yet")
                            return self.current_phase
                
                return new_phase
                
            except ValueError:
                print(f"Invalid phase name received: {phase_name}")
                return self.current_phase
            
        except Exception as e:
            print(f"Error in phase analysis: {str(e)}")
            return self.current_phase
    
    def _prepare_conversation_context(self) -> str:
        """Prepares the conversation history for analysis."""
        # Get the last 5 messages for context
        recent_messages = self.conversation_history[-5:]
        
        # Format the conversation
        formatted_conversation = []
        for msg in recent_messages:
            speaker = "Agent" if msg["is_agent"] else "Customer"
            formatted_conversation.append(f"{speaker}: {msg['message']}")
        
        return "\n".join(formatted_conversation)
    
    def _update_phase(self, new_phase: ConversationPhase):
        """Updates the current phase and records the transition."""
        if new_phase != self.current_phase:
            self.phase_history.append({
                "from_phase": self.current_phase,
                "to_phase": new_phase,
                "timestamp": time.time(),
                "conversation_length": len(self.conversation_history)
            })
            self.current_phase = new_phase
    
    def is_closing_phase(self) -> bool:
        """Checks if the conversation is in the closing phase."""
        return self.current_phase == ConversationPhase.CLOSING
    
    def get_phase_history(self) -> List[Dict]:
        """Returns the history of phase transitions."""
        return self.phase_history
    
    def get_current_phase(self) -> ConversationPhase:
        """Returns the current conversation phase."""
        return self.current_phase