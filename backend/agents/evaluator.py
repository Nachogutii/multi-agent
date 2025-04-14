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
        self._analyze_introduction_discovery_phase()
        self._analyze_value_proposition_phase()
        self._analyze_objection_handling_phase()
        self._analyze_closing_phase()
        
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
    
    def _analyze_introduction_discovery_phase(self):
        """Analyzes the introduction and discovery phase effectiveness."""
        # Check for pain point discovery
        if self.pain_points:
            score.adjust_score(5)
            score.add_strength("Successfully identified customer pain points")
        else:
            score.add_feedback("Could have done more to uncover customer pain points")
            score.add_suggestion("Ask more probing questions about current challenges")
        
        # Check for goal identification
        goal_indicators = ["goal", "objective", "target", "aim", "want to achieve"]
        found_goals = any(indicator in message["user"].lower() or indicator in message["customer"].lower()
                         for message in self.conversation_history 
                         for indicator in goal_indicators)
        
        if found_goals:
            score.adjust_score(5)
            score.add_strength("Effectively identified customer goals")
        else:
            score.add_feedback("Could have better understood customer objectives")
            score.add_suggestion("Ask about specific business goals and desired outcomes")
        
        # Check for needs analysis
        needs_indicators = ["need", "requirement", "looking for", "seeking", "want"]
        found_needs = any(indicator in message["user"].lower() or indicator in message["customer"].lower()
                         for message in self.conversation_history 
                         for indicator in needs_indicators)
        
        if found_needs:
            score.adjust_score(5)
            score.add_strength("Good understanding of customer needs")
        else:
            score.add_feedback("Could have better explored customer needs")
            score.add_suggestion("Ask more questions about specific requirements")
        
        # Check for industry context
    def _analyze_value_proposition_phase(self):
        """Analyzes the value proposition phase effectiveness."""
        # Check for value proposition clarity
        value_indicators = ["benefit", "value", "roi", "improve", "enhance", "increase"]
        found_value = any(indicator in message["user"].lower() or indicator in message["customer"].lower()
                         for message in self.conversation_history 
                         for indicator in value_indicators)
        
        if found_value:
            score.adjust_score(5)
            score.add_strength("Clear communication of value proposition")
        else:
            score.add_feedback("Could have better articulated product value")
            score.add_suggestion("Focus more on specific benefits and ROI")
        
        # Check for pain point alignment
        if self.pain_points and found_value:
            score.adjust_score(5)
            score.add_strength("Effectively aligned value with pain points")
        else:
            score.add_missed_opportunity("Could have better connected value to customer pain points")
        
        # Check for business impact
        impact_indicators = ["impact", "result", "outcome", "improvement", "change"]
        found_impact = any(indicator in message["user"].lower() or indicator in message["customer"].lower()
                          for message in self.conversation_history 
                          for indicator in impact_indicators)
        
        if found_impact:
            score.adjust_score(5)
            score.add_strength("Strong focus on business impact")
        else:
            score.add_feedback("Could have better emphasized business impact")
            score.add_suggestion("Include more specific examples of business outcomes")
        
        # Check for ROI discussion
        roi_indicators = ["roi", "return on investment", "cost savings", "efficiency"]
        found_roi = any(indicator in message["user"].lower() or indicator in message["customer"].lower()
                       for message in self.conversation_history 
                       for indicator in roi_indicators)
        
        if found_roi:
            score.adjust_score(5)
            score.add_strength("Effective ROI discussion")
        else:
            score.add_missed_opportunity("Could have included more ROI analysis")
    
    def _analyze_objection_handling_phase(self):
        """Analyzes the objection handling phase effectiveness."""
        # Check for objection acknowledgment
        if self.objections:
            score.adjust_score(5)
            score.add_strength("Identified and acknowledged customer objections")
        else:
            score.add_missed_opportunity("Could have proactively addressed potential objections")
        
        # Check for empathy in responses
        empathy_indicators = ["understand", "appreciate", "recognize", "hear", "feel"]
        found_empathy = any(indicator in message["user"].lower() or indicator in message["customer"].lower()
                          for message in self.conversation_history 
                          for indicator in empathy_indicators)
        
        if found_empathy:
            score.adjust_score(5)
            score.add_strength("Demonstrated empathy in responses")
        else:
            score.add_feedback("Could have shown more empathy in responses")
            score.add_suggestion("Acknowledge concerns before addressing them")
        
        # Check for value-driven responses
        # Check for blocker resolution
        if self.blockers:
            resolution_indicators = ["solution", "address", "resolve", "overcome", "handle"]
            found_resolution = any(indicator in message["user"].lower() or indicator in message["customer"].lower()
                                 for message in self.conversation_history 
                                 for indicator in resolution_indicators)
            
            if found_resolution:
                score.adjust_score(5)
                score.add_strength("Effectively addressed blockers")
            else:
                score.add_feedback("Could have better addressed blockers")
                score.add_suggestion("Provide specific solutions for identified blockers")
    
    def _analyze_closing_phase(self):
        """Analyzes the closing phase effectiveness."""
        # Check for next steps
        next_step_indicators = ["next step", "follow up", "schedule", "plan", "arrange"]
        found_next_steps = any(indicator in message["user"].lower() or indicator in message["customer"].lower()
                             for message in self.conversation_history 
                             for indicator in next_step_indicators)
        
        if found_next_steps:
            score.adjust_score(5)
            score.add_strength("Clear next steps established")
        else:
            score.add_feedback("Could have established clearer next steps")
            score.add_suggestion("Outline specific follow-up actions")
        
        # Check for success metrics
        metric_indicators = ["measure", "track", "monitor", "evaluate", "assess"]
        found_metrics = any(indicator in message["user"].lower() or indicator in message["customer"].lower()
                          for message in self.conversation_history 
                          for indicator in metric_indicators)
        
        if found_metrics:
            score.adjust_score(5)
            score.add_strength("Discussed success metrics")
        else:
            score.add_missed_opportunity("Could have discussed success metrics")
        
        # Check for expansion opportunities
        expansion_indicators = ["expand", "grow", "scale", "additional", "more"]
        found_expansion = any(indicator in message["user"].lower() or indicator in message["customer"].lower()
                            for message in self.conversation_history 
                            for indicator in expansion_indicators)
        
        if found_expansion:
            score.adjust_score(5)
            score.add_strength("Identified expansion opportunities")
        else:
            score.add_missed_opportunity("Could have discussed expansion opportunities")
        
        # Check for support discussion
        support_indicators = ["support", "help", "assist", "guide", "resource"]
        found_support = any(indicator in message["user"].lower() or indicator in message["customer"].lower()
                          for message in self.conversation_history 
                          for indicator in support_indicators)
        
        if found_support:
            score.adjust_score(5)
            score.add_strength("Addressed support and resources")
        else:
            score.add_feedback("Could have discussed support options")
            score.add_suggestion("Outline available support and resources")
    
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
        self._analyze_introduction_discovery_phase()
        self._analyze_value_proposition_phase()
        self._analyze_objection_handling_phase()
        self._analyze_closing_phase()
        
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