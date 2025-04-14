import time
from typing import Dict, List, Tuple
from agents.conversation_phase import ConversationPhaseManager
import json
import re


class ObserverCoach:
    """Analyzes user interaction with the customer and provides feedback."""

    def __init__(self, azure_client=None, deployment=None):
        if azure_client is None:
            raise ValueError("Azure OpenAI client not initialized in ObserverCoach.")
        self.client = azure_client
        self.deployment = deployment
        self.conversation_history = []
        self.score = 0
        self.max_score = 100
        self.feedback_points = []
        self.phase_manager = ConversationPhaseManager(azure_client, deployment)
        self.pain_points = []
        self.objections = []
        self.blockers = []
        self.has_evaluated_closing = False
        self.cumulative_fulfilled_aspects = set()

    def evaluate_interaction_with_llm(self, user_message: str, customer_response: str) -> Dict[str, any]:
        if not self.client:
            raise ValueError("Azure OpenAI client not initialized")
        if not self.deployment:
            raise ValueError("Azure OpenAI deployment not set")
        
        current_phase = self.phase_manager.get_current_phase()
        current_phase_config = self.phase_manager.phase_config.get_phase(current_phase)
        current_guidelines = current_phase_config.success_criteria if current_phase_config else []


        prompt = f"""
        Evaluate the following interaction between a Microsoft support agent and a customer.
        Based on the current phase of the conversation, identify how many key aspects are fulfilled.

        PHASE: {current_phase}
        KEY ASPECTS:
        - {chr(10).join(current_guidelines)}

        AGENT MESSAGE:
        {user_message}

        CUSTOMER RESPONSE:
        {customer_response}

        Return a JSON with the following keys:
        - fulfilled_aspects: a list of the fulfilled key aspects (from the list above)
        - progress: a percentage (0 to 100) of how many key aspects were fulfilled
        - CustomerBelievesAgentIsEmpathetic: boolean
        - CustomerBelievesAgentIsLegit: boolean

        Format example:
        {{
            "fulfilled_aspects": ["understanding customer context", "identifying customer role"],
            "progress": 40,
            "CustomerBelievesAgentIsEmpathetic": true,
            "CustomerBelievesAgentIsLegit": true
        }}
        """

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are a senior customer experience analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )

            raw_output = response.choices[0].message.content
            print(f"🧠 Raw Evaluator Output:\n{raw_output}")

            # Limpia bloques ```json o ``` y deja solo el JSON
            cleaned_output = raw_output.strip()
            if cleaned_output.startswith("```json"):
                cleaned_output = cleaned_output[len("```json"):].strip()
            if cleaned_output.endswith("```"):
                cleaned_output = cleaned_output[:-3].strip()

            return json.loads(cleaned_output)

        except Exception as e:
            print(f"⚠️ Error parsing JSON from evaluator output: {e}")
            return {
                "fulfilled_aspects": [],
                "progress": 0,
                "CustomerBelievesAgentIsEmpathetic": False,
                "CustomerBelievesAgentIsLegit": False
            }


        except Exception as e:
            print(f"⚠️ Error evaluating with LLM: {e}")
            return {
                "fulfilled_aspects": [],
                "progress": 0,
                "CustomerBelievesAgentIsEmpathetic": False,
                "CustomerBelievesAgentIsLegit": False
            }


    def update_customer_state(self, user_message: str, customer_response: str) -> Dict[str, any]:
        evaluation_result = self.evaluate_interaction_with_llm(user_message, customer_response)

        new_aspects = set(evaluation_result.get("fulfilled_aspects", []))
        self.cumulative_fulfilled_aspects.update(new_aspects)

        current_phase = self.phase_manager.get_current_phase()
        current_config = self.phase_manager.phase_config.get_phase(current_phase)
        total_aspects = len(current_config.success_criteria) if current_config else 1
        progress = round((len(self.cumulative_fulfilled_aspects) / total_aspects) * 100)

        updated_state = {
            "fulfilled_aspects": list(self.cumulative_fulfilled_aspects),
            "progress": progress,
            "CustomerBelievesAgentIsEmpathetic": evaluation_result.get("CustomerBelievesAgentIsEmpathetic", False),
            "CustomerBelievesAgentIsLegit": evaluation_result.get("CustomerBelievesAgentIsLegit", False)
        }

        new_phase = self.phase_manager.analyze_message(user_message, customer_response)
        print(f"📍 Transitioned to phase: {new_phase}")

        return updated_state



    def add_interaction(self, user_message: str, customer_response: str):
        # Evalúa el mensaje con LLM (incluye empatía, legitimidad y aspectos cumplidos)
        evaluation_result = self.evaluate_interaction_with_llm(user_message, customer_response)
        print(f"✅ Evaluation Result: {evaluation_result}")

        # Decide fase usando el resultado completo
        current_phase = self.phase_manager.decide_phase(evaluation_result)
        print(f"📊 Phase decided by LLM: {current_phase}")

        # Guarda en el historial
        self.conversation_history.append({
            "user": user_message,
            "customer": customer_response,
            "timestamp": time.time(),
            "phase": current_phase
        })

        # Analiza preocupaciones del cliente
        self._analyze_customer_concerns(customer_response)
        
        # For debugging
        print(f"Updated Customer State: {evaluation_result}")

        # Evalúa cierre si es la última fase
    
    def _analyze_customer_concerns(self, message: str):
        """Analyzes message for pain points, objections, and blockers."""
        # Pain point indicators
        pain_point_indicators = [
            "struggle", "difficult", "challenge", "problem", "issue",
            "frustrated", "pain", "hassle", "complicated", "time-consuming"
        ]
        
        # Objection indicators
        objection_indicators = [
            "expensive", "cost", "price", "budget", "concerned",
            "worried", "hesitant", "not sure", "doubt", "risk"
        ]
        
        # Blocker indicators
        blocker_indicators = [
            "can't", "unable", "impossible", "blocked", "restricted",
            "limitation", "constraint", "barrier", "obstacle", "hurdle"
        ]
        
        message_lower = message.lower()
        
        # Extract pain points
        for indicator in pain_point_indicators:
            if indicator in message_lower:
                self.pain_points.append(message)
                break
        
        # Extract objections
        for indicator in objection_indicators:
            if indicator in message_lower:
                self.objections.append(message)
                break
        
        # Extract blockers
        for indicator in blocker_indicators:
            if indicator in message_lower:
                self.blockers.append(message)
                break
    
    def analyze_conversation(self) -> Dict:
        """Analyzes the conversation and provides comprehensive feedback."""
        if not self.conversation_history:
            return {
                "score": 0,
                "feedback": ["No interactions to analyze."],
                "suggestions": ["Start a conversation to receive feedback."]
            }
        
        # Reset phase scores
        for score in self.phase_scores.values():
            score.score = 0
            score.feedback = []
            score.suggestions = []
            score.strengths = []
            score.missed_opportunities = []
        
        # Analyze each phase
        self._analyze_welcome_phase()
        self._analyze_abrupt_closure_phase()
        self._analyze_copilot_positive_experience_phase()
        self._analyze_business_goal_phase()
        self._analyze_value_add_phase()
        self._analyze_polite_closure_phase()
        self._analyze_satisfied_closure_phase()
        self._analyze_copilot_negative_experiences_phase()
        self._analyze_copilot_negative_experience_handling_phase()
        
        # Calculate overall score
        total_score = sum(score.score for score in self.phase_scores.values())
        
        # Compile feedback
        feedback = []
        suggestions = []
        strengths = []
        missed_opportunities = []
        
        for phase_score in self.phase_scores.values():
            feedback.extend(phase_score.feedback)
            suggestions.extend(phase_score.suggestions)
            strengths.extend(phase_score.strengths)
            missed_opportunities.extend(phase_score.missed_opportunities)
        
        return {
            "score": total_score,
            "phase_scores": {phase.value: score.score for phase, score in self.phase_scores.items()},
            "feedback": list(set(feedback)),
            "suggestions": list(set(suggestions)),
            "strengths": list(set(strengths)),
            "missed_opportunities": list(set(missed_opportunities)),
            "pain_points": self.pain_points,
            "objections": self.objections,
            "blockers": self.blockers
        }
    
    def _analyze_welcome_phase(self):
        """Analyzes the welcome phase effectiveness."""
        # Check for proper introduction
        if any("name" in message["user"].lower() for message in self.conversation_history):
            score.adjust_score(5)
            score.add_strength("Agent properly introduced themselves")
        else:
            score.add_feedback("Agent did not introduce themselves")
            score.add_suggestion("Ensure to state your name and affiliation")

        # Check for purpose clarity
        if any("purpose" in message["user"].lower() for message in self.conversation_history):
            score.adjust_score(5)
            score.add_strength("Agent clearly stated the purpose of the call")
        else:
            score.add_feedback("Agent did not state the purpose of the call")
            score.add_suggestion("Clearly state the purpose of the call")

    def _analyze_abrupt_closure_phase(self):
        """Analyzes the abrupt closure phase effectiveness."""
        # Check for professional closure
        if any("apologize" in message["user"].lower() for message in self.conversation_history):
            score.adjust_score(5)
            score.add_strength("Agent apologized appropriately")
        else:
            score.add_feedback("Agent did not apologize appropriately")
            score.add_suggestion("Apologize to the customer when closing abruptly")

    def _analyze_copilot_positive_experience_phase(self):
        """Analyzes the Copilot positive experience phase effectiveness."""
        # Check for positive feedback acknowledgment
        if any("thank" in message["user"].lower() for message in self.conversation_history):
            score.adjust_score(5)
            score.add_strength("Agent acknowledged positive feedback")
        else:
            score.add_feedback("Agent did not acknowledge positive feedback")
            score.add_suggestion("Thank the customer for positive feedback")

    def _analyze_business_goal_phase(self):
        """Analyzes the business goal phase effectiveness."""
        # Check for goal alignment
        if any("goal" in message["user"].lower() for message in self.conversation_history):
            score.adjust_score(5)
            score.add_strength("Agent aligned with business goals")
        else:
            score.add_feedback("Agent did not align with business goals")
            score.add_suggestion("Discuss business goals with the customer")

    def _analyze_value_add_phase(self):
        """Analyzes the value add phase effectiveness."""
        # Check for value proposition
        if any("value" in message["user"].lower() for message in self.conversation_history):
            score.adjust_score(5)
            score.add_strength("Agent provided value proposition")
        else:
            score.add_feedback("Agent did not provide value proposition")
            score.add_suggestion("Discuss the value proposition with the customer")

    def _analyze_polite_closure_phase(self):
        """Analyzes the polite closure phase effectiveness."""
        # Check for polite closure
        if any("thank" in message["user"].lower() for message in self.conversation_history):
            score.adjust_score(5)
            score.add_strength("Agent closed the call politely")
        else:
            score.add_feedback("Agent did not close the call politely")
            score.add_suggestion("Thank the customer when closing the call")

    def _analyze_satisfied_closure_phase(self):
        """Analyzes the satisfied closure phase effectiveness."""
        # Check for satisfaction confirmation
        if any("satisfied" in message["user"].lower() for message in self.conversation_history):
            score.adjust_score(5)
            score.add_strength("Agent confirmed customer satisfaction")
        else:
            score.add_feedback("Agent did not confirm customer satisfaction")
            score.add_suggestion("Confirm customer satisfaction before closing")

    def _analyze_copilot_negative_experiences_phase(self):
        """Analyzes the Copilot negative experiences phase effectiveness."""
        # Check for negative feedback acknowledgment
        if any("sorry" in message["user"].lower() for message in self.conversation_history):
            score.adjust_score(5)
            score.add_strength("Agent acknowledged negative feedback")
        else:
            score.add_feedback("Agent did not acknowledge negative feedback")
            score.add_suggestion("Acknowledge negative feedback appropriately")

    def _analyze_copilot_negative_experience_handling_phase(self):
        """Analyzes the Copilot negative experience handling phase effectiveness."""
        # Check for transition to positive
        if any("positive" in message["user"].lower() for message in self.conversation_history):
            score.adjust_score(5)
            score.add_strength("Agent transitioned to positive experiences")
        else:
            score.add_feedback("Agent did not transition to positive experiences")
            score.add_suggestion("Transition to positive experiences after handling negatives")
    
    def _generate_ai_feedback(self, phase: str, context: str) -> Dict:
        """Generates AI-powered feedback for a specific phase."""
        if not self.client or not self.deployment:
            return {"feedback": "", "suggestion": "", "strength": "", "opportunity": ""}
            
        prompt = f"""
        Analyze this conversation phase and provide comprehensive, actionable feedback.

        Phase: {phase.value}
        Conversation Context:
        {context}

        Consider these aspects in your analysis:

        1. Natural Flow and Progression:
           - How well did the conversation flow through this phase?
           - Were there smooth transitions between topics?
           - Was the progression logical and natural?

        2. Relationship Development:
           - How well was rapport maintained?
           - Was there appropriate emotional intelligence?
           - How effectively was trust built?

        3. Content Quality:
           - How relevant and valuable was the information shared?
           - Was the communication clear and effective?
           - Were key points well-articulated?

        4. Customer Engagement:
           - How well was the customer engaged?
           - Were questions and concerns addressed?
           - Was there appropriate give-and-take?

        5. Phase-Specific Effectiveness:
           - How well were phase-specific goals achieved?
           - Were there missed opportunities?
           - What could have been done better?

        Provide:
        1. Specific feedback about strengths and areas for improvement
        2. Concrete, actionable suggestions
        3. Insights about the overall effectiveness
        4. Recommendations for future conversations

        Format the response as JSON with:
        {
            "feedback": "Detailed analysis of what was done well and what could be improved",
            "suggestion": "Specific, actionable suggestion for improvement",
            "strength": "Key strength observed in this phase",
            "opportunity": "Missed opportunity or area for growth"
        }
        """
        
        try:
            result = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": """You are an expert conversation evaluator.
                    Your task is to provide detailed, actionable feedback on conversation phases.
                    Focus on natural flow, relationship development, and effectiveness.
                    Provide specific, practical suggestions for improvement.
                    Return the response in the specified JSON format."""},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3,
            )
            
            # Parse the response as JSON
            import json
            try:
                feedback_data = json.loads(result.choices[0].message.content)
                return {
                    "feedback": feedback_data.get("feedback", ""),
                    "suggestion": feedback_data.get("suggestion", ""),
                    "strength": feedback_data.get("strength", ""),
                    "opportunity": feedback_data.get("opportunity", "")
                }
            except:
                return {"feedback": "", "suggestion": "", "strength": "", "opportunity": ""}
                
        except Exception as e:
            print(f"Error generating AI feedback: {e}")
            return {"feedback": "", "suggestion": "", "strength": "", "opportunity": ""}
    
    def _evaluate_closing_phase(self):
        """Performs a comprehensive evaluation of the conversation when entering the closing phase."""
        # Analyze each phase
        self._analyze_welcome_phase()
        self._analyze_abrupt_closure_phase()
        self._analyze_copilot_positive_experience_phase()
        self._analyze_business_goal_phase()
        self._analyze_value_add_phase()
        self._analyze_polite_closure_phase()
        self._analyze_satisfied_closure_phase()
        self._analyze_copilot_negative_experiences_phase()
        self._analyze_copilot_negative_experience_handling_phase()
        
        # Calculate phase coverage
        covered_phases = set()
        for message in self.conversation_history:
            if message.get("phase"):
                covered_phases.add(message["phase"])
        
        # Evaluate phase transitions
        phase_transitions = []
        for i in range(1, len(self.conversation_history)):
            if self.conversation_history[i].get("phase") != self.conversation_history[i-1].get("phase"):
                phase_transitions.append({
                    "from": self.conversation_history[i-1].get("phase"),
                    "to": self.conversation_history[i].get("phase")
                })
        
        # Generate comprehensive AI feedback for each phase
        for phase in covered_phases:
            # Create context for the phase
            phase_messages = [msg for msg in self.conversation_history if msg.get("phase") == phase]
            context = "\n".join([f"{msg['user']}\n{msg['customer']}" for msg in phase_messages])
            
            # Get AI feedback
            ai_feedback = self._generate_ai_feedback(phase, context)
            if ai_feedback["feedback"]:
                self.phase_scores[phase].add_feedback(ai_feedback["feedback"])
            if ai_feedback["suggestion"]:
                self.phase_scores[phase].add_suggestion(ai_feedback["suggestion"])
            if ai_feedback["strength"]:
                self.phase_scores[phase].add_strength(ai_feedback["strength"])
            if ai_feedback["opportunity"]:
                self.phase_scores[phase].add_missed_opportunity(ai_feedback["opportunity"])
        
        # Generate comprehensive feedback
        self._generate_comprehensive_feedback(covered_phases, phase_transitions)
    
    def _generate_comprehensive_feedback(self):
        """Generates final summary based on dynamic phases and phase transitions."""
        covered_phases = {entry["to"] for entry in self.phase_manager.get_phase_history()}
        covered_phases.add(self.phase_manager.get_current_phase())  # Include last phase even if not transitioned

        all_phase_names = set(self.phase_manager.phase_config.get_all_phase_names())
        missing_phases = all_phase_names - covered_phases
        transitions = self.phase_manager.get_phase_history()

        summary = "\n=== COMPREHENSIVE CONVERSATION EVALUATION ===\n"

        summary += "\n🧩 Phase Coverage:\n"
        for phase in self.phase_manager.phase_config.get_all_phase_names():
            if phase in covered_phases:
                summary += f"✅ {phase}\n"
            else:
                summary += f"❌ {phase} - Not covered\n"

        summary += "\n🔁 Phase Transitions:\n"
        if transitions:
            for t in transitions:
                summary += f"• {t['from']} → {t['to']}\n"
        else:
            summary += "No phase transitions detected.\n"

        summary += "\n📌 Observations:\n"
        if self.pain_points:
            summary += f"• Detected {len(self.pain_points)} pain points.\n"
        if self.objections:
            summary += f"• Detected {len(self.objections)} objections.\n"
        if self.blockers:
            summary += f"• Detected {len(self.blockers)} blockers.\n"

        if missing_phases:
            summary += "\n🧠 Recommendations:\n"
            for phase in missing_phases:
                summary += f"• Consider covering the {phase} phase in future conversations.\n"

        self.comprehensive_summary = summary

    
    def _generate_final_summary(self, total_score: int, phase_scores: Dict, covered_phases: set, phase_transitions: List[Dict]):
        """Generates a final comprehensive summary of the conversation."""
        summary = "\n=== COMPREHENSIVE CONVERSATION EVALUATION ===\n"
        
        # Overall Score
        summary += f"\nOverall Score: {total_score}/{self.max_score}\n"
        
        # Phase Coverage
        summary += "\nPhase Coverage:\n"
        for phase in ConversationPhase:
            if phase in covered_phases:
                summary += f"✓ {phase.value}: {phase_scores.get(phase.value, 0)}/20\n"
            else:
                summary += f"✗ {phase.value}: Not covered\n"
        
        # Phase Transitions
        summary += "\nPhase Transitions:\n"
        if phase_transitions:
            for transition in phase_transitions:
                summary += f"• {transition['from'].value} → {transition['to'].value}\n"
        else:
            summary += "Limited phase transitions observed\n"
        
        # Strengths
        summary += "\nKey Strengths:\n"
        for phase_score in self.phase_scores.values():
            for strength in phase_score.strengths:
                summary += f"• {strength}\n"
        
        # Areas for Improvement
        summary += "\nAreas for Improvement:\n"
        for phase_score in self.phase_scores.values():
            for feedback in phase_score.feedback:
                summary += f"• {feedback}\n"
        
        # Recommendations
        summary += "\nRecommendations:\n"
        for phase_score in self.phase_scores.values():
            for suggestion in phase_score.suggestions:
                summary += f"• {suggestion}\n"
        
        # Customer Concerns
        if self.pain_points:
            summary += "\nIdentified Pain Points:\n"
            for point in self.pain_points:
                summary += f"• {point}\n"
        
        if self.objections:
            summary += "\nCustomer Objections:\n"
            for objection in self.objections:
                summary += f"• {objection}\n"
        
        if self.blockers:
            summary += "\nIdentified Blockers:\n"
            for blocker in self.blockers:
                summary += f"• {blocker}\n"
        
        # Store the comprehensive summary
        self.comprehensive_summary = summary
    
    def get_summary(self) -> str:
        """Returns the comprehensive summary if available, otherwise returns the basic analysis."""
        # If we have a comprehensive summary (from closing phase), return it
        if hasattr(self, 'comprehensive_summary'):
            return self.comprehensive_summary
            
        # If we're in the closing phase but haven't generated the summary yet, do it now
        if self.phase_manager.is_closing_phase() and not self.has_evaluated_closing:
            self._evaluate_closing_phase()
            self.has_evaluated_closing = True
            return self.comprehensive_summary
            
        # Otherwise, return the basic analysis
        return self.analyze_conversation() 