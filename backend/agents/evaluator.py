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

        self.phase_scores = {}  # Score per phase
        self.phase_feedback = {}  # Detailed feedback per phase
        self.phase_optional_aspects = {}  # Fulfilled optional aspects per phase

    def evaluate_interaction_with_llm(self, user_message: str, customer_response: str) -> Dict[str, any]:
        if not self.client:
            raise ValueError("Azure OpenAI client not initialized")
        if not self.deployment:
            raise ValueError("Azure OpenAI deployment not set")
        
        current_phase = self.phase_manager.get_current_phase()
        current_phase_config = self.phase_manager.phase_config.get_phase(current_phase)
        current_critical_aspects = current_phase_config.critical_aspects if current_phase_config else []


        prompt = f"""
        Evaluate the following interaction between a Microsoft support agent and a customer.
        Based on the current phase of the conversation, identify how many key aspects are fulfilled.

        PHASE: {current_phase}
        KEY ASPECTS:
        - {chr(10).join(current_critical_aspects)}

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

            # Clean JSON format more thoroughly
            cleaned_output = raw_output.strip()
            # Remove ```json and ``` if they exist
            if "```json" in cleaned_output:
                cleaned_output = cleaned_output.replace("```json", "")
            if "```" in cleaned_output:
                cleaned_output = cleaned_output.replace("```", "")
            
            # Remove any text before or after the JSON
            start_bracket = cleaned_output.find('{')
            end_bracket = cleaned_output.rfind('}')
            if start_bracket != -1 and end_bracket != -1:
                cleaned_output = cleaned_output[start_bracket:end_bracket + 1]
            
            try:
                return json.loads(cleaned_output)
            except Exception as e:
                print(f"⚠️ Error parsing JSON: {e}")
                print(f"⚠️ Cleaned output: {cleaned_output}")
                # Try a basic fallback
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

        # Get the CURRENT phase before analyzing the message
        current_phase = self.phase_manager.get_current_phase()
        print(f"🔍 Current phase before analysis: {current_phase}")
        
        # Now, analyze the message for phase transition
        # This is the ONLY place where we should call analyze_message
        new_phase = self.phase_manager.analyze_message(user_message, customer_response)
        print(f"📍 Phase transition evaluated: {current_phase} -> {new_phase}")
        
        # Get configuration for the UPDATED phase
        updated_phase = self.phase_manager.get_current_phase()
        current_config = self.phase_manager.phase_config.get_phase(updated_phase)
        
        # Use the accumulated critical aspects from phase_manager
        cumulative_aspects = self.phase_manager.get_cumulative_critical_aspects(updated_phase)
        
        # Combine with aspects detected by the evaluator
        all_fulfilled_aspects = list(set(cumulative_aspects + list(self.cumulative_fulfilled_aspects)))
        
        # Fix: Ensure total_aspects is never zero to avoid division by zero error
        # For phases like "Conversation End" with no critical aspects, set progress to 100%
        if current_config and hasattr(current_config, 'critical_aspects') and current_config.critical_aspects:
            total_aspects = len(current_config.critical_aspects)
            progress = round((len(all_fulfilled_aspects) / max(1, total_aspects)) * 100) if total_aspects > 0 else 100
        else:
            # If we're in a terminal phase or a phase with no critical aspects, progress is 100%
            progress = 100
            print("ℹ️ In terminal phase or no critical aspects defined - setting progress to 100%")

        # Get global counters to include in the updated state
        aspect_counts = self.phase_manager.get_aspect_counts()

        updated_state = {
            "fulfilled_aspects": all_fulfilled_aspects,
            "progress": min(100, progress),  # Ensure it doesn't exceed 100%
            "CustomerBelievesAgentIsEmpathetic": evaluation_result.get("CustomerBelievesAgentIsEmpathetic", False),
            "CustomerBelievesAgentIsLegit": evaluation_result.get("CustomerBelievesAgentIsLegit", False),
            "aspect_counts": aspect_counts  # Include global counters in the state
        }

        # Record fulfilled optional aspects
        if updated_phase not in self.phase_optional_aspects:
            self.phase_optional_aspects[updated_phase] = []
        
        # Add optional aspects if they are in optional_aspects_fulfilled from phase_manager
        optional_aspects = self.phase_manager.get_optional_aspects_fulfilled()
        if optional_aspects:
            for aspect in optional_aspects:
                if aspect not in self.phase_optional_aspects[updated_phase]:
                    self.phase_optional_aspects[updated_phase].append(aspect)

        # Show the updated phase after analysis
        print(f"🔍 Current phase after analysis: {self.phase_manager.get_current_phase()}")
        
        # Log of updated global counters
        print(f"📊 Global counters: Critical: {aspect_counts['critical_aspects']}, " +
              f"Optional: {aspect_counts['optional_aspects']}, " +
              f"Red flags: {aspect_counts['red_flags']}")

        return updated_state



    def add_interaction(self, user_message: str, customer_response: str):
        # Evaluate the message with LLM
        evaluation_result = self.evaluate_interaction_with_llm(user_message, customer_response)
        
        # Get the updated state that includes accumulated aspects
        updated_state = self.update_customer_state(user_message, customer_response)
        
        print(f"✅ Evaluation Result: {evaluation_result}")
        print(f"👑 Accumulated Aspects: {updated_state['fulfilled_aspects']}")
        print(f"📊 Progress: {updated_state['progress']}%")

        # Important: we must use the current phase from phase_manager after update_customer_state
        current_phase = self.phase_manager.get_current_phase()
        print(f"📊 Current updated phase: {current_phase}")
        
        # Save the interaction with phase and timestamp
        self.conversation_history.append({
            "user": user_message,
            "customer": customer_response,
            "timestamp": time.time(),
            "phase": current_phase,
            "fulfilled_aspects": updated_state['fulfilled_aspects'],  # Save fulfilled aspects
            "progress": updated_state['progress']  # Save progress
        })

        # Evaluate the current phase if not done yet
        current_context = "\n".join([
            f"User: {m['user']}\nCustomer: {m['customer']}"
            for m in self.conversation_history
            if m.get("phase") == current_phase
        ])
        if current_context.strip() and current_phase not in self.phase_scores:
            print(f"🧠 Evaluating current phase: {current_phase}")
            self.evaluate_phase(current_phase, current_context)

        # Analyze customer concerns
        self._analyze_customer_concerns(customer_response)

        print(f"📝 Updated Customer State: {updated_state}")
        print(f"📝 Final phase after interaction: {self.phase_manager.get_current_phase()}")

    
    
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
            "can't", "cannot", "won't", "impossible", "never",
            "deal-breaker", "show-stopper", "unacceptable", "no way"
        ]
        
        message_lower = message.lower()
        
        # Check for pain points
        for indicator in pain_point_indicators:
            if indicator in message_lower:
                self.pain_points.append(message)
                break
                
        # Check for objections
        for indicator in objection_indicators:
            if indicator in message_lower:
                self.objections.append(message)
                break
                
        # Check for blockers
        for indicator in blocker_indicators:
            if indicator in message_lower:
                self.blockers.append(message)
                break
    
    def evaluate_phase(self, phase: str, context: str) -> Dict[str, any]:
        """Evaluates a specific phase and provides detailed feedback."""
        if not context.strip():
            return {
                "score": 0,
                "feedback": "Not enough context to evaluate this phase."
            }
            
        # Get phase configuration
        phase_config = self.phase_manager.phase_config.get_phase(phase)
        if not phase_config:
            return {
                "score": 0,
                "feedback": f"Phase '{phase}' not found in configuration."
            }
            
        # Get critical and optional aspects
        critical_aspects = phase_config.critical_aspects
        red_flags = phase_config.red_flags
        optional_aspects = phase_config.optional_aspects
            
        # Get detailed feedback from AI
        ai_feedback = self._generate_ai_feedback(phase, context, critical_aspects, red_flags, optional_aspects)
        
        # Get accumulated critical aspects for this phase
        accumulated_aspects = self.phase_manager.get_cumulative_critical_aspects(phase)
        
        # Combine aspects detected by AI with accumulated ones
        aspects_met = list(set(ai_feedback.get("aspects_met", []) + accumulated_aspects))
        
        flags_triggered = ai_feedback.get("flags_triggered", [])
        optional_met = ai_feedback.get("optional_met", [])
        
        # Store fulfilled optional aspects
        self.phase_optional_aspects[phase] = optional_met
            
        # Calculate score
        if flags_triggered:
            score = 0  # If there are red flags, score is zero
        else:
            # Base: percentage of fulfilled critical aspects
            critical_score = (len(aspects_met) / max(1, len(critical_aspects))) * 100
            
            # Bonus for optional aspects (maximum 20% additional)
            optional_bonus = min(20, (len(optional_met) / max(1, len(optional_aspects))) * 20)
            
            score = min(100, round(critical_score + optional_bonus))
        
        # Save score and feedback
        self.phase_scores[phase] = score
        self.phase_feedback[phase] = {
            "strength": ai_feedback.get("strength", ""),
            "opportunity": ai_feedback.get("opportunity", ""),
            "suggestion": ai_feedback.get("suggestion", ""),
            "training": ai_feedback.get("training", ""),
            "aspects_met": aspects_met,
            "flags_triggered": flags_triggered,
            "optional_met": optional_met
        }
            
        return {
            "score": score,
            "feedback": self.phase_feedback[phase]
        }
    
    def _generate_ai_feedback(self, phase: str, context: str, critical_aspects=None, red_flags=None, optional_aspects=None) -> Dict:
        """Generates detailed feedback using AI."""
        if not critical_aspects:
            # Use default values if not provided
            phase_config = self.phase_manager.phase_config.get_phase(phase)
            if phase_config:
                critical_aspects = phase_config.critical_aspects
                red_flags = phase_config.red_flags
                optional_aspects = phase_config.optional_aspects
            else:
                return {}
                
        # Get previously accumulated aspects
        accumulated_critical_aspects = self.phase_manager.get_cumulative_critical_aspects(phase)
        
        # Create complete conversation context
        full_context = context
        if not full_context.strip():
            # If there's no specific context, build it from the complete history
            full_context = "\n".join([
                f"User: {m['user']}\nCustomer: {m['customer']}"
                for m in self.conversation_history
            ])
                
        prompt = f"""
        Analyze this Microsoft customer service conversation during the "{phase}" phase.

        CONVERSATION CONTEXT:
        {full_context}

        CRITICAL ASPECTS THAT SHOULD BE MET:
        {chr(10).join('- ' + c for c in critical_aspects)}

        RED FLAGS THAT SHOULD NOT OCCUR:
        {chr(10).join('- ' + f for f in red_flags)}

        OPTIONAL ASPECTS (NICE TO HAVE):
        {chr(10).join('- ' + o for o in optional_aspects)}
        
        ASPECTS ALREADY MET IN PREVIOUS INTERACTIONS:
        {chr(10).join('- ' + a for a in accumulated_critical_aspects) if accumulated_critical_aspects else "None"}

        Evaluate the entire conversation (not just the last message) and return only a JSON object with the following fields:
        - aspects_met: array of critical aspects that were met throughout the conversation
        - flags_triggered: array of red flags that occurred (empty if none)
        - optional_met: array of optional aspects met (empty if none)
        - strength: a main strength demonstrated by the agent (concise).
        - opportunity: a clear improvement opportunity (concise)
        - suggestion: specific suggestion to improve
        - training: concept or skill the agent should focus on

        Format:
        {{
            "aspects_met": ["aspect 1", "aspect 2"],
            "flags_triggered": ["red flag 1", "red flag 2"],
            "optional_met": ["optional 1", "optional 2"],
            "strength": "The agent demonstrated excellent..."
            "opportunity": "The agent could improve in...",
            "suggestion": "We recommend that the agent...",
            "training": "Training in active listening..."
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are an expert coach in customer service evaluation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.2
            )
            
            feedback = response.choices[0].message.content.strip()
            
            # Improved JSON cleaning
            cleaned_feedback = feedback
            
            # Remove ```json and ``` if they exist
            if "```json" in cleaned_feedback:
                cleaned_feedback = cleaned_feedback.replace("```json", "")
            if "```" in cleaned_feedback:
                cleaned_feedback = cleaned_feedback.replace("```", "")
            
            # Remove any text before or after the JSON
            start_bracket = cleaned_feedback.find('{')
            end_bracket = cleaned_feedback.rfind('}')
            if start_bracket != -1 and end_bracket != -1:
                cleaned_feedback = cleaned_feedback[start_bracket:end_bracket + 1]
            
            cleaned_feedback = cleaned_feedback.strip()
            
            try:
                result = json.loads(cleaned_feedback)
                # Make sure to include already fulfilled aspects
                if accumulated_critical_aspects:
                    all_aspects = list(set(result.get("aspects_met", []) + accumulated_critical_aspects))
                    result["aspects_met"] = all_aspects
                return result
            except Exception as e:
                print(f"Error parsing JSON: {feedback}")
                print(f"Cleaned feedback: {cleaned_feedback}")
                print(f"Specific error: {str(e)}")
                return {"aspects_met": accumulated_critical_aspects}
            
        except Exception as e:
            print(f"Error generating AI feedback: {e}")
            return {"aspects_met": accumulated_critical_aspects}
    
    
    def summarize_conversation(self) -> Dict[str, any]:
        """Generates a complete summary of the conversation with detailed feedback."""
        # If all phases haven't been evaluated, evaluate them
        all_phases_in_history = list({m.get("phase") for m in self.conversation_history if m.get("phase")})
        for phase in all_phases_in_history:
            if phase and phase not in self.phase_scores:
                context = "\n".join([
                    f"User: {m['user']}\nCustomer: {m['customer']}"
                    for m in self.conversation_history
                    if m.get("phase") == phase
                ])
                if context.strip():
                    self.evaluate_phase(phase, context)

        # Also evaluate the closing phase if applicable
        if self.phase_manager.is_closing_phase() and not self.has_evaluated_closing:
            self._evaluate_closing_phase()
            self.has_evaluated_closing = True

        # Generate summary
        phase_transitions = self.phase_manager.get_phase_history()
        covered_phases = set(self.phase_scores.keys())
        
        # Calculate total score
        total_score = 0
        phases_count = 0
        
        for phase, score in self.phase_scores.items():
            if score > 0:  # Only count phases with a score
                total_score += score
                phases_count += 1
                
        avg_score = total_score / max(1, phases_count)
        
        # Include fulfilled optional aspects in the feedback
        phase_feedback_with_optional = {}
        for phase, feedback in self.phase_feedback.items():
            phase_feedback_with_optional[phase] = feedback.copy()
            if phase in self.phase_optional_aspects:
                phase_feedback_with_optional[phase]["optional_aspects_met"] = self.phase_optional_aspects.get(phase, [])
        
        # Get global counters of aspects and flags
        aspect_counts = self.phase_manager.get_aspect_counts()
        
        # Calculate custom score based on counters
        custom_score_data = self.calculate_custom_score()
        
        return {
            "total_score": round(avg_score),
            "custom_score": custom_score_data,  # Add custom score to summary
            "phase_scores": self.phase_scores,
            "feedback": phase_feedback_with_optional,
            "summary": self._generate_final_summary(
                round(avg_score), 
                self.phase_scores,
                covered_phases,
                phase_transitions
            ),
            "pain_points": self.pain_points,
            "objections": self.objections,
            "blockers": self.blockers,
            "aspect_counts": aspect_counts  # Add global counters to summary
        }

    def _evaluate_closing_phase(self):
        """Performs a comprehensive evaluation of the conversation when entering the closing phase."""
        # If all phases haven't been evaluated, evaluate them
        all_phases_in_history = list({m.get("phase") for m in self.conversation_history if m.get("phase")})
        for phase in all_phases_in_history:
            if phase and phase not in self.phase_scores:
                context = "\n".join([
                    f"User: {m['user']}\nCustomer: {m['customer']}"
                    for m in self.conversation_history
                    if m.get("phase") == phase
                ])
                if context.strip():
                    self.evaluate_phase(phase, context)
                    
        # Generate comprehensive feedback
        self._generate_comprehensive_feedback()
        
        # Mark as evaluated
        self.has_evaluated_closing = True
        
    def _generate_comprehensive_feedback(self):
        """Generates comprehensive feedback based on dynamic phases and phase transitions."""
        covered_phases = {entry["to"] for entry in self.phase_manager.get_phase_history()}
        covered_phases.add(self.phase_manager.get_current_phase())  # Include current phase
        
        # Get all phase names from config
        all_phase_names = self.phase_manager.phase_config.phase_order
        missing_phases = [p for p in all_phase_names if p not in covered_phases]
        transitions = self.phase_manager.get_phase_history()
        
        # Get global counters of aspects and flags
        aspect_counts = self.phase_manager.get_aspect_counts()
        total_critical_aspects = aspect_counts["critical_aspects"]
        total_optional_aspects = aspect_counts["optional_aspects"]
        total_red_flags = aspect_counts["red_flags"]
        
        # Calculate custom score
        custom_score_data = self.calculate_custom_score()
        custom_score = custom_score_data["score"]
        custom_score_explanation = custom_score_data["explanation"]
        
        summary = "\n=== COMPREHENSIVE CONVERSATION EVALUATION ===\n"
        
        # Overall score
        total_score = 0
        phases_count = 0
        for phase, score in self.phase_scores.items():
            if score > 0:  # Only count phases with a score
                total_score += score
                phases_count += 1
        
        avg_score = total_score / max(1, phases_count)
        summary += f"\nOverall score (phase average): {round(avg_score)}/100\n"
        
        # Add custom score to summary
        summary += f"\n🎯 CUSTOM SCORE: {custom_score}/100\n"
        summary += f"{custom_score_explanation}\n"
        
        # Add summary of global counters
        summary += f"\n📊 CRITICAL AND OPTIONAL ASPECTS FULFILLED 📊\n"
        summary += f"✅ Critical aspects fulfilled: {total_critical_aspects}\n"
        summary += f"🌟 Optional aspects fulfilled: {total_optional_aspects}\n"
        summary += f"⚠️ Red flags detected: {total_red_flags}\n"
        
        # Phase coverage
        summary += "\nPhase Coverage:\n"
        for phase in all_phase_names:
            if phase in covered_phases:
                score = self.phase_scores.get(phase, 0)
                summary += f"✅ {phase}: {score}/100\n"
            else:
                summary += f"❌ {phase} - Not covered\n"
        
        # Phase transitions
        summary += "\n🔁 Phase Transitions:\n"
        if transitions:
            for t in transitions:
                summary += f"• {t['from']} → {t['to']}\n"
        else:
            summary += "No phase transitions detected.\n"
        
        # Strengths and opportunities
        summary += "\n💪 Key Strengths:\n"
        for phase, feedback in self.phase_feedback.items():
            if feedback.get("strength"):
                summary += f"• {phase}: {feedback['strength']}\n"
        
        summary += "\n🔧 Opportunities for Improvement:\n"
        for phase, feedback in self.phase_feedback.items():
            if feedback.get("opportunity"):
                summary += f"• {phase}: {feedback['opportunity']}\n"
        
        # Suggestions
        summary += "\n💡 Recommendations:\n"
        for phase, feedback in self.phase_feedback.items():
            if feedback.get("suggestion"):
                summary += f"• {phase}: {feedback['suggestion']}\n"
        
        # Customer concerns
        if self.pain_points:
            summary += "\n⚠️ Identified Pain Points:\n"
            for point in self.pain_points:
                summary += f"• {point}\n"
        
        if self.objections:
            summary += "\n🚩 Customer Objections:\n"
            for objection in self.objections:
                summary += f"• {objection}\n"
        
        if self.blockers:
            summary += "\n🛑 Identified Blockers:\n"
            for blocker in self.blockers:
                summary += f"• {blocker}\n"
        
        # Store the comprehensive summary
        self.comprehensive_summary = summary
        
    def _generate_final_summary(self, total_score, phase_scores, covered_phases, phase_transitions):
        """Generates a final summary of the conversation evaluation."""
        # Use the _generate_comprehensive_feedback method to generate a summary
        self._generate_comprehensive_feedback()
        return self.comprehensive_summary
    
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
        return self.summarize_conversation()

    def calculate_custom_score(self) -> Dict[str, any]:
        """
        Calculates a custom score based on global aspect counters.
        
        The formula is:
        - Base score: 0 points
        - Each critical aspect: +20 points
        - Each optional aspect: +10 points
        - Each red flag: -40 points
        
        The result is normalized to a 0-100 scale, considering that the theoretical
        maximum is 420 points (if all aspects are fulfilled in all phases).
        """
        # Get current global counters
        aspect_counts = self.phase_manager.get_aspect_counts()
        critical_count = aspect_counts["critical_aspects"]
        optional_count = aspect_counts["optional_aspects"] 
        red_flags_count = aspect_counts["red_flags"]
        
        # Direct calculation based on counters
        base_score = 0
        critical_points = 20  # points per critical aspect
        optional_points = 10  # points per optional aspect
        red_flag_penalty = 40  # points deducted per red flag
        
        # Calculate each component
        critical_bonus = critical_count * critical_points
        optional_bonus = optional_count * optional_points
        penalty = red_flags_count * red_flag_penalty
        
        # Simple calculation of final score (on 0-420 scale)
        raw_score = base_score + critical_bonus + optional_bonus - penalty
        
        # Ensure score is not negative
        raw_score = max(0, raw_score)
        
        # Normalize to 0-100 scale (theoretical maximum is 420)
        max_theoretical_score = 420
        normalized_score = round((raw_score / max_theoretical_score) * 100)
        
        # Calculation details for explanation
        score_details = {
            "base_score": base_score,
            "critical_bonus": critical_bonus,
            "optional_bonus": optional_bonus,
            "red_flags_penalty": -penalty,
            "raw_score": raw_score,
            "normalized_score": normalized_score
        }
        
        # Textual explanation of calculation
        explanation = (
            f"Base score: {base_score}\n"
            f"Critical aspects: +{critical_bonus} ({critical_count} × {critical_points} points)\n"
            f"Optional aspects: +{optional_bonus} ({optional_count} × {optional_points} points)\n"
            f"Red flags: -{penalty} ({red_flags_count} × {red_flag_penalty} points)\n"
            f"Raw score: {raw_score} (scale 0-420)\n"
            f"Normalized score: {normalized_score}/100"
        )
        
        return {
            "score": normalized_score,
            "details": score_details,
            "explanation": explanation,
            "aspect_counts": aspect_counts
        } 