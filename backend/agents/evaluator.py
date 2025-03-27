import time
from typing import Dict, List, Tuple
from agents.conversation_phase import ConversationPhase, ConversationPhaseManager

class PLGPhaseScore:
    """Tracks scoring and feedback for each PLG phase."""
    
    def __init__(self, phase: ConversationPhase, max_score: int = 20):
        self.phase = phase
        self.max_score = max_score
        self.score = 0
        self.feedback = []
        self.suggestions = []
        self.strengths = []
        self.missed_opportunities = []
    
    def add_feedback(self, feedback: str, suggestion: str = None):
        """Adds feedback and optional suggestion."""
        self.feedback.append(feedback)
        if suggestion:
            self.suggestions.append(suggestion)
    
    def add_suggestion(self, suggestion: str):
        """Adds a suggestion for improvement."""
        self.suggestions.append(suggestion)
    
    def add_strength(self, strength: str):
        """Adds a strength observation."""
        self.strengths.append(strength)
    
    def add_missed_opportunity(self, opportunity: str):
        """Adds a missed opportunity observation."""
        self.missed_opportunities.append(opportunity)
    
    def adjust_score(self, points: int):
        """Adjusts the score within max_score limits."""
        self.score = min(max(0, self.score + points), self.max_score)

class ObserverCoach:
    """Analyzes user interaction with the customer and provides feedback."""
    
    def __init__(self, azure_client=None, deployment=None):
        self.conversation_history = []
        self.score = 0
        self.max_score = 100
        self.feedback_points = []
        self.phase_manager = ConversationPhaseManager()
        self.phase_scores = {
            phase: PLGPhaseScore(phase) for phase in ConversationPhase
        }
        self.pain_points = []
        self.objections = []
        self.blockers = []
        self.has_evaluated_closing = False
        self.client = azure_client
        self.deployment = deployment
    
    def add_interaction(self, user_message: str, customer_response: str):
        """Adds an interaction to the conversation history."""
        current_phase = self.phase_manager.analyze_message(user_message)
        self.conversation_history.append({
            "user": user_message,
            "customer": customer_response,
            "timestamp": time.time(),
            "phase": current_phase
        })
        
        # Analyze for pain points, objections, and blockers
        self._analyze_customer_concerns(customer_response)
        
        # If entering closing phase and hasn't been evaluated yet, perform comprehensive evaluation
        if current_phase == ConversationPhase.CLOSING and not self.has_evaluated_closing:
            # Print the customer's closing message first
            print(f"\nCustomer: {customer_response}")
            # Then show the evaluation
            print("\n=== CONVERSATION EVALUATION ===")
            self._evaluate_closing_phase()
            self.has_evaluated_closing = True
            print(self.get_summary())
    
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
        self._analyze_discovery_phase()
        self._analyze_value_alignment_phase()
        self._analyze_product_experience_phase()
        self._analyze_objection_handling_phase()
        self._analyze_follow_up_phase()
        
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
    
    def _analyze_discovery_phase(self):
        """Analyzes the discovery phase effectiveness."""
        score = self.phase_scores[ConversationPhase.DISCOVERY]
        
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
        if any(message.get("phase") == ConversationPhase.DISCOVERY 
               for message in self.conversation_history):
            score.adjust_score(5)
            score.add_strength("Maintained focus on industry-specific context")
        else:
            score.add_missed_opportunity("Could have explored industry-specific challenges")
    
    def _analyze_value_alignment_phase(self):
        """Analyzes the value alignment phase effectiveness."""
        score = self.phase_scores[ConversationPhase.VALUE_ALIGNMENT]
        
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
    
    def _analyze_product_experience_phase(self):
        """Analyzes the product experience phase effectiveness."""
        score = self.phase_scores[ConversationPhase.PRODUCT_EXPERIENCE]
        
        # Check for demo/trial discussion
        demo_indicators = ["demo", "demonstration", "trial", "try", "experience", "hands-on"]
        found_demo = any(indicator in message["user"].lower() or indicator in message["customer"].lower()
                        for message in self.conversation_history 
                        for indicator in demo_indicators)
        
        if found_demo:
            score.adjust_score(5)
            score.add_strength("Proactively offered product experience")
        else:
            score.add_feedback("Could have offered product demonstration")
            score.add_suggestion("Suggest a demo or trial to showcase value")
        
        # Check for implementation discussion
        implementation_indicators = ["implement", "deploy", "setup", "configure", "integrate"]
        found_implementation = any(indicator in message["user"].lower() or indicator in message["customer"].lower()
                                 for message in self.conversation_history 
                                 for indicator in implementation_indicators)
        
        if found_implementation:
            score.adjust_score(5)
            score.add_strength("Addressed implementation considerations")
        else:
            score.add_missed_opportunity("Could have discussed implementation details")
        
        # Check for technical requirements
        tech_indicators = ["technical", "requirement", "compatibility", "integration", "system"]
        found_tech = any(indicator in message["user"].lower() or indicator in message["customer"].lower()
                        for message in self.conversation_history 
                        for indicator in tech_indicators)
        
        if found_tech:
            score.adjust_score(5)
            score.add_strength("Addressed technical requirements")
        else:
            score.add_feedback("Could have better addressed technical aspects")
            score.add_suggestion("Discuss technical requirements and compatibility")
        
        # Check for user adoption
        adoption_indicators = ["adoption", "training", "learn", "use", "utilize"]
        found_adoption = any(indicator in message["user"].lower() or indicator in message["customer"].lower()
                           for message in self.conversation_history 
                           for indicator in adoption_indicators)
        
        if found_adoption:
            score.adjust_score(5)
            score.add_strength("Addressed user adoption considerations")
        else:
            score.add_missed_opportunity("Could have discussed user adoption strategy")
    
    def _analyze_objection_handling_phase(self):
        """Analyzes the objection handling phase effectiveness."""
        score = self.phase_scores[ConversationPhase.OBJECTION_HANDLING]
        
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
        if found_empathy and any(message.get("phase") == ConversationPhase.VALUE_ALIGNMENT 
                               for message in self.conversation_history):
            score.adjust_score(5)
            score.add_strength("Connected objections to value proposition")
        else:
            score.add_feedback("Could have better connected responses to value")
            score.add_suggestion("Link solutions to customer value")
        
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
    
    def _analyze_follow_up_phase(self):
        """Analyzes the follow-up phase effectiveness."""
        score = self.phase_scores[ConversationPhase.FOLLOW_UP]
        
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
    
    def _generate_ai_feedback(self, phase: ConversationPhase, context: str) -> Dict:
        """Generates AI-powered feedback for a specific phase."""
        if not self.client or not self.deployment:
            return {"feedback": "", "suggestion": ""}
            
        prompt = f"""
Analyze this conversation phase and provide specific, actionable feedback.

Phase: {phase.value}
Context: {context}

Provide:
1. Specific feedback about what was done well and what could be improved
2. A concrete suggestion for improvement
3. Focus on practical, actionable advice

Format the response as JSON with "feedback" and "suggestion" fields.
"""
        try:
            result = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "Please analyze this conversation phase and provide feedback."}
                ],
                max_tokens=300,
                temperature=0.3,
            )
            
            # Parse the response as JSON
            import json
            try:
                return json.loads(result.choices[0].message.content)
            except:
                return {"feedback": "", "suggestion": ""}
                
        except Exception as e:
            print(f"Error generating AI feedback: {e}")
            return {"feedback": "", "suggestion": ""}
    
    def _evaluate_closing_phase(self):
        """Performs a comprehensive evaluation of the conversation when entering the closing phase."""
        # Analyze each phase
        self._analyze_discovery_phase()
        self._analyze_value_alignment_phase()
        self._analyze_product_experience_phase()
        self._analyze_objection_handling_phase()
        self._analyze_follow_up_phase()
        
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
        
        # Generate AI-powered feedback for each phase
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
        
        # Generate comprehensive feedback
        self._generate_comprehensive_feedback(covered_phases, phase_transitions)
    
    def _generate_comprehensive_feedback(self, covered_phases: set, phase_transitions: List[Dict]):
        """Generates comprehensive feedback based on the conversation analysis."""
        # Phase Coverage Analysis
        required_phases = {
            ConversationPhase.DISCOVERY,
            ConversationPhase.VALUE_ALIGNMENT,
            ConversationPhase.PRODUCT_EXPERIENCE,
            ConversationPhase.OBJECTION_HANDLING,
            ConversationPhase.FOLLOW_UP
        }
        
        missing_phases = required_phases - covered_phases
        
        # Add feedback for missing phases
        for phase in missing_phases:
            self.phase_scores[phase].add_feedback(f"Phase {phase.value} was not covered in the conversation")
            self.phase_scores[phase].add_suggestion(f"Ensure to cover {phase.value} phase in future conversations")
        
        # Add feedback for phase transitions
        if len(phase_transitions) < 2:
            self.phase_scores[ConversationPhase.DISCOVERY].add_feedback("Limited phase transitions observed")
            self.phase_scores[ConversationPhase.DISCOVERY].add_suggestion("Work on smoother transitions between phases")
        
        # Add contextual insights
        if self.pain_points:
            self.phase_scores[ConversationPhase.DISCOVERY].add_strength(f"Identified {len(self.pain_points)} key pain points")
        if self.objections:
            self.phase_scores[ConversationPhase.OBJECTION_HANDLING].add_strength(f"Handled {len(self.objections)} customer objections")
        if self.blockers:
            self.phase_scores[ConversationPhase.OBJECTION_HANDLING].add_feedback(f"Identified {len(self.blockers)} potential blockers")
        
        # Calculate final scores
        total_score = sum(score.score for score in self.phase_scores.values())
        phase_scores = {phase.value: score.score for phase, score in self.phase_scores.items()}
        
        # Generate final summary
        self._generate_final_summary(total_score, phase_scores, covered_phases, phase_transitions)
    
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