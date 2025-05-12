from typing import List, Dict
import time
from openai import AzureOpenAI
from phase_config import ConversationPhaseConfig

class ConversationPhaseManager:
    def __init__(self, azure_client=None, deployment=None):
        self.client = azure_client
        self.deployment = deployment
        self.conversation_history: List[Dict] = []
        self.phase_config = ConversationPhaseConfig()  
        self.current_phase = self.phase_config.get_initial_phase()  
        self.phase_history: List[Dict] = []
        self.optional_aspects_fulfilled = []  # Para almacenar aspectos opcionales cumplidos para feedback
        self.cumulative_critical_aspects = {}  # Para mantener aspectos críticos cumplidos por fase
        self.cumulative_red_flags = {}  # Para mantener red flags detectadas por fase
        
        # Contadores globales para aspectos cumplidos en toda la conversación
        self.total_critical_aspects_count = 0
        self.total_optional_aspects_count = 0
        self.total_red_flags_count = 0
        
        # Sets para mantener registro único de aspectos/flags detectados
        self.unique_critical_aspects = set()
        self.unique_optional_aspects = set()
        self.unique_red_flags = set()

    def add_message(self, message: str, is_agent: bool = True):
        self.conversation_history.append({
            "message": message,
            "is_agent": is_agent,
            "timestamp": time.time()
        })

    def analyze_message(self, agent_message: str, customer_response: str) -> str:
        print(f"📊 INPUT: analyze_message - Current phase: {self.current_phase}")
        current_config = self.phase_config.get_phase(self.current_phase)

        # Special handling for terminal phases - don't allow transitions out of these
        if self.current_phase == "Conversation End":
            print("🛑🛑🛑 TERMINAL PHASE 'Conversation End' ACTIVE - NO TRANSITIONS ALLOWED")
            print("🛑🛑🛑 ALL SUBSEQUENT INTERACTIONS WILL BE CLOSING RESPONSES")
            return self.current_phase

        # Special handling for "Abrupt closure" phase - only allow transition to "Conversation End"
        if self.current_phase == "Abrupt closure":
            print("⚠️ In Abrupt closure phase - customer is ending the conversation")
            # Don't check for critical aspects or red flags, just move to Conversation End
            prev_phase = self.current_phase
            self._record_phase_transition("Conversation End")
            print(f"🛑🛑🛑 TRANSITION FROM '{prev_phase}' TO TERMINAL PHASE 'Conversation End' - CLOSING CONVERSATION")
            print(f"🛑🛑🛑 FINAL STATE: current_phase = {self.current_phase}")
            print(f"📊 OUTPUT: analyze_message - New phase: {self.current_phase}")
            return "Conversation End"

        # Create context of all previous conversation plus current message
        conversation_context = []
        
        # Add previous messages from history
        for msg in self.conversation_history[-5:]:  # Last 5 messages for context
            if msg.get("is_agent", False):
                conversation_context.append(f"Agent: {msg['message']}")
            else:
                conversation_context.append(f"Customer: {msg['message']}")
                
        # Add current message and response
        conversation_context.append(f"Agent: {agent_message}")
        conversation_context.append(f"Customer: {customer_response}")
        
        full_context = "\n".join(conversation_context)
        
        # 1. First check if there are red flags (if there are, we go directly to failure)
        red_flags_result = self._check_red_flags(agent_message, customer_response, full_context)
        
        # Print raw message for debugging explicit offensive terms
        print(f"DEBUG - Raw agent message: '{agent_message}'")
        
        # Accumulate detected red flags for current phase
        if self.current_phase not in self.cumulative_red_flags:
            self.cumulative_red_flags[self.current_phase] = []
            
        # Add new red flags to accumulated list
        for flag in red_flags_result.get("red_flags_found", []):
            if flag not in self.cumulative_red_flags[self.current_phase]:
                self.cumulative_red_flags[self.current_phase].append(flag)
        
        # CRITICAL: ENSURE red flags are detected and honored
        if red_flags_result.get("has_red_flags", False):
            print(f"⚠️ RED FLAGS DETECTED: {red_flags_result.get('red_flags_found')}")
            print(f"⚠️ IMMEDIATE TRANSITION TO: {current_config.failure_transition}")
            # Always transition to failure state immediately if red flags detected
            new_phase = current_config.failure_transition
            prev_phase = self.current_phase
            self._record_phase_transition(new_phase)
            print(f"📊 RED FLAG TRANSITION: {prev_phase} -> {self.current_phase}")
            
            # If the new state is Abrupt Closure, check if we should go directly to Conversation End
            if self.current_phase == "Abrupt closure":
                print("⚠️⚠️⚠️ Automatic transition from Abrupt closure to Conversation End")
                prev_phase = self.current_phase
                self._record_phase_transition("Conversation End")
                print(f"🛑🛑🛑 TRANSITION FROM '{prev_phase}' TO TERMINAL PHASE 'Conversation End' - CLOSING CONVERSATION")
                print(f"🛑🛑🛑 FINAL STATE: current_phase = {self.current_phase}")
            
            print(f"📊 OUTPUT: analyze_message - New phase (after red flags): {self.current_phase}")
            return self.current_phase
        
        # 2. Evaluate critical aspects for advancement, considering complete context
        critical_aspects_result = self._check_critical_aspects(agent_message, customer_response, full_context)
        
        # Accumulate fulfilled critical aspects for current phase
        if self.current_phase not in self.cumulative_critical_aspects:
            self.cumulative_critical_aspects[self.current_phase] = []
            
        # Add new critical aspects to accumulated list
        for aspect in critical_aspects_result.get("aspects_met", []):
            if aspect not in self.cumulative_critical_aspects[self.current_phase]:
                self.cumulative_critical_aspects[self.current_phase].append(aspect)
        
        # Also check optional aspects (for feedback only, doesn't affect transition)
        self._check_optional_aspects(agent_message, customer_response, full_context)
        
        # Determine if we advance by comparing accumulated aspects against all critical ones
        all_critical_aspects = current_config.critical_aspects
        accumulated_aspects = self.cumulative_critical_aspects.get(self.current_phase, [])
        
        # Show current progress
        print(f"✅ Accumulated critical aspects: {accumulated_aspects}")
        print(f"🎯 Required critical aspects: {all_critical_aspects}")
        
        # Proceed to next phase if all critical aspects are met
        all_critical_met = all(aspect in accumulated_aspects for aspect in all_critical_aspects)
        
        if all_critical_met:
            new_phase = current_config.success_transition
            print(f"✨ All critical aspects fulfilled! Advancing to phase: {new_phase}")
            prev_phase = self.current_phase
            self._record_phase_transition(new_phase)
            print(f"📊 SUCCESS TRANSITION: {prev_phase} -> {self.current_phase}")
            
            # If the new state is Conversation End, we should mark it as terminal
            if self.current_phase == "Conversation End":
                print("🛑🛑🛑 REACHED TERMINAL PHASE 'Conversation End' - NO MORE TRANSITIONS ALLOWED")
                print(f"🛑🛑🛑 FINAL STATE: current_phase = {self.current_phase}")
            
            print(f"📊 OUTPUT: analyze_message - New phase (after success): {self.current_phase}")
            return self.current_phase
        else:
            # Stay in current phase
            missing_aspects = [aspect for aspect in all_critical_aspects if aspect not in accumulated_aspects]
            print(f"⏳ Pending critical aspects: {missing_aspects}")
            print(f"📊 OUTPUT: analyze_message - Phase unchanged: {self.current_phase}")
            return self.current_phase

    def _check_red_flags(self, agent_message: str, customer_response: str, full_context: str = None) -> Dict:
        """Checks if there are red flags in the current interaction."""
        current_config = self.phase_config.get_phase(self.current_phase)
        red_flags = current_config.red_flags
        
        # Special handling for Abrupt closure phase - no red flags should be detected here
        # as this phase is already a result of red flags
        if self.current_phase == "Abrupt closure":
            return {"has_red_flags": False, "red_flags_found": []}
        
        if not red_flags:
            return {"has_red_flags": False, "red_flags_found": []}
        
        # Use full context if available
        context_section = ""
        if full_context:
            context_section = f"""
    ## FULL CONVERSATION CONTEXT
    {full_context}
            """
            
        # Include information about the current phase to provide context
        phase_context = f"""
    ## CURRENT CONVERSATION PHASE
    {self.current_phase}
        """
            
        prompt = f"""
    You are evaluating a customer service interaction to check for RED FLAGS - serious issues that would cause the conversation to fail immediately.
    
    ## RED FLAGS TO CHECK
    {chr(10).join('- ' + f for f in red_flags)}
    {phase_context}
    
    ## AGENT MESSAGE
    {agent_message}
    
    ## CUSTOMER RESPONSE
    {customer_response}
    {context_section}
    
    IMPORTANT: ONLY evaluate the AGENT's message (not the customer's) for red flags.
    If the agent uses any offensive language, rude statements, dismissive tone, or unprofessional behavior, this must be flagged.
    Examples of behavior that MUST be flagged as red flags:
    - Profanity or explicit language (e.g., f-word, s-word, etc.)
    - Telling the customer to go away or to use another service
    - Using dismissive phrases like "don't bother me" or "I'm too busy"
    - Making any discriminatory comments
    - Being confrontational or aggressive
    
    Return ONLY a JSON with two fields:
    - "has_red_flags": boolean (true ONLY if clear violations exist in the AGENT's message)
    - "red_flags_found": list of specific red flags found (empty if none)
    """
        
        try:
            print(f"Checking for red flags in phase: {self.current_phase}")
            
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are a conversation evaluator focused on identifying only serious problematic behavior by the agent (Microsoft representative). Be strict and precise."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0
            )
            
            result = response.choices[0].message.content.strip()
            print(f"Red flag raw response: {result}")
            
            import json
            try:
                # Clean JSON result from backticks and code markers
                cleaned_result = result
                if "```json" in cleaned_result:
                    cleaned_result = cleaned_result.replace("```json", "")
                if "```" in cleaned_result:
                    cleaned_result = cleaned_result.replace("```", "")
                cleaned_result = cleaned_result.strip()
                
                # Extract JSON if embedded in other text
                start_bracket = cleaned_result.find('{')
                end_bracket = cleaned_result.rfind('}')
                if start_bracket != -1 and end_bracket != -1:
                    cleaned_result = cleaned_result[start_bracket:end_bracket + 1]
                
                result_json = json.loads(cleaned_result)
                
                # Direct keyword detection for obvious offensive terms
                agent_msg_lower = agent_message.lower()
                
                # List of explicitly offensive terms that should always be flagged
                explicit_offensive_terms = ["fuck", "shit", "bitch", "ass", "damn", "hell", "crap", 
                                          "asshole", "bastard", "stupid", "idiot", "dumb", "moron"]
                
                # List of dismissive/rude phrases
                dismissive_phrases = ["dont bother", "don't bother", "go away", "leave me", "busy", 
                                    "chatgpt", "chatgot", "chat gpt", "shut up", "hang up"]
                
                has_explicit_terms = any(term in agent_msg_lower for term in explicit_offensive_terms)
                has_dismissive_phrases = any(term in agent_msg_lower for term in dismissive_phrases)
                
                # If we detect an explicit offensive term but the LLM missed it, override
                if (has_explicit_terms or has_dismissive_phrases) and not result_json.get("has_red_flags", False):
                    print("⚠️ Overriding LLM decision - explicit offensive or dismissive language detected")
                    found_terms = []
                    if has_explicit_terms:
                        found_terms.append("Agent uses explicit offensive language")
                    if has_dismissive_phrases:
                        found_terms.append("Agent uses dismissive or unprofessional language")
                    
                    result_json["has_red_flags"] = True
                    result_json["red_flags_found"] = found_terms
                
                print(f"Final red flags result: {result_json}")
                
                # Actualizar contadores globales de red flags
                red_flags_found = result_json.get("red_flags_found", [])
                if red_flags_found:
                    # Incrementar contador por cada nueva bandera roja encontrada
                    for flag in red_flags_found:
                        if flag not in self.unique_red_flags:
                            self.unique_red_flags.add(flag)
                            self.total_red_flags_count += 1
                
                return result_json
            except Exception as e:
                print(f"Error parsing JSON from red flags check: {result}")
                print(f"Specific error: {str(e)}")
                
                # Even if there's an error, check for explicit terms as a fallback
                agent_msg_lower = agent_message.lower()
                explicit_terms = ["fuck", "shit", "bitch", "asshole", "idiot", "stupid", "shut up", "go away"]
                if any(term in agent_msg_lower for term in explicit_terms):
                    # Actualizar contador global si se detecta bandera roja
                    flag_message = "Agent uses explicit offensive language"
                    if flag_message not in self.unique_red_flags:
                        self.unique_red_flags.add(flag_message)
                        self.total_red_flags_count += 1
                    return {"has_red_flags": True, "red_flags_found": [flag_message]}
                
                # Default to no red flags if parsing fails and no explicit terms found
                return {"has_red_flags": False, "red_flags_found": []}
                
        except Exception as e:
            print(f"Error checking red flags: {str(e)}")
            
            # Even with API errors, still check for explicit terms
            agent_msg_lower = agent_message.lower()
            explicit_terms = ["fuck", "shit", "bitch", "asshole", "idiot", "stupid", "shut up", "go away"]
            if any(term in agent_msg_lower for term in explicit_terms):
                # Actualizar contador global si se detecta bandera roja
                flag_message = "Agent uses explicit offensive language"
                if flag_message not in self.unique_red_flags:
                    self.unique_red_flags.add(flag_message)
                    self.total_red_flags_count += 1
                return {"has_red_flags": True, "red_flags_found": [flag_message]}
                
            return {"has_red_flags": False, "red_flags_found": []}
            
    def _check_critical_aspects(self, agent_message: str, customer_response: str, full_context: str = None) -> Dict:
        """Checks which critical aspects have been fulfilled."""
        current_config = self.phase_config.get_phase(self.current_phase)
        critical_aspects = current_config.critical_aspects
        
        if not critical_aspects:
            return {"all_critical_met": True, "aspects_met": []}
        
        # Use full context if available
        context_section = ""
        if full_context:
            context_section = f"""
    ## FULL CONVERSATION CONTEXT
    {full_context}
            """
            
        # Include aspects already met for the LLM to consider
        already_met = self.cumulative_critical_aspects.get(self.current_phase, [])
        already_met_section = ""
        if already_met:
            already_met_section = f"""
    ## ASPECTS ALREADY MET IN PREVIOUS MESSAGES
    {chr(10).join('- ' + a for a in already_met)}
            """
            
        prompt = f"""
    You are evaluating a customer service interaction for CRITICAL ASPECTS that must be fulfilled.
    
    ## CRITICAL ASPECTS TO CHECK
    {chr(10).join('- ' + c for c in critical_aspects)}
    
    ## AGENT MESSAGE
    {agent_message}
    
    ## CUSTOMER RESPONSE
    {customer_response}
    {context_section}
    {already_met_section}
    
    IMPORTANT INSTRUCTIONS:
    - Be very flexible in your assessment
    - If there's any reasonable evidence the aspect was fulfilled, count it as met
    - Focus on concepts rather than exact wording
    - Allow for variations in how requirements are expressed
    - When in doubt, consider the aspect fulfilled
    
    Return ONLY a JSON with two fields:
    - "all_critical_met": boolean (true only if ALL critical aspects are met)
    - "aspects_met": list of specific aspects that were met (include previously met aspects)
    """
        
        try:
            print(f"Checking critical aspects in phase: {self.current_phase}")
            
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are a conversation evaluator focused on identifying fulfilled requirements. Be very generous in your evaluation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0
            )
            
            result = response.choices[0].message.content.strip()
            print(f"Critical aspects raw response: {result}")
            
            import json
            try:
                # Clean JSON result from backticks and code markers
                cleaned_result = result
                if "```json" in cleaned_result:
                    cleaned_result = cleaned_result.replace("```json", "")
                if "```" in cleaned_result:
                    cleaned_result = cleaned_result.replace("```", "")
                cleaned_result = cleaned_result.strip()
                
                # Extract JSON if embedded in other text
                start_bracket = cleaned_result.find('{')
                end_bracket = cleaned_result.rfind('}')
                if start_bracket != -1 and end_bracket != -1:
                    cleaned_result = cleaned_result[start_bracket:end_bracket + 1]
                
                result_json = json.loads(cleaned_result)
                
                # Simple fallback detection for welcome phase
                if self.current_phase == "welcome":
                    agent_msg_lower = agent_message.lower()
                    aspects_met = result_json.get("aspects_met", [])
                    
                    # Check for Microsoft mention
                    if "microsoft" in agent_msg_lower and "Agent mentions they are from Microsoft" not in aspects_met:
                        aspects_met.append("Agent mentions they are from Microsoft")
                        
                    # Check for Copilot mention
                    if "copilot" in agent_msg_lower and "Agent mentions Microsoft Copilot" not in aspects_met:
                        aspects_met.append("Agent mentions Microsoft Copilot")
                        
                    result_json["aspects_met"] = aspects_met
                
                # Make sure to include previously met aspects
                combined_aspects = list(set(result_json.get("aspects_met", []) + already_met))
                result_json["aspects_met"] = combined_aspects
                result_json["all_critical_met"] = all(aspect in combined_aspects for aspect in critical_aspects)
                
                # Actualizar contadores globales de aspectos críticos
                new_aspects = [aspect for aspect in result_json.get("aspects_met", []) if aspect not in already_met]
                for aspect in new_aspects:
                    if aspect not in self.unique_critical_aspects:
                        self.unique_critical_aspects.add(aspect)
                        self.total_critical_aspects_count += 1
                
                print(f"Final critical aspects result: {result_json}")
                return result_json
            except Exception as e:
                print(f"Error parsing JSON from critical aspects check: {result}")
                print(f"Specific error: {str(e)}")
                # Return at least previously met aspects if there's an error
                return {"all_critical_met": False, "aspects_met": already_met}
                
        except Exception as e:
            print(f"Error checking critical aspects: {str(e)}")
            return {"all_critical_met": False, "aspects_met": already_met}
            
    def _check_optional_aspects(self, agent_message: str, customer_response: str, full_context: str = None) -> Dict:
        """Checks which optional aspects (nice to have) have been fulfilled."""
        current_config = self.phase_config.get_phase(self.current_phase)
        optional_aspects = current_config.optional_aspects
        
        if not optional_aspects:
            return {"aspects_met": []}
        
        # Use full context if available
        context_section = ""
        if full_context:
            context_section = f"""
    ## FULL CONVERSATION CONTEXT
    {full_context}
            """
            
        prompt = f"""
    You are evaluating a customer service interaction for OPTIONAL ASPECTS that improve the quality.
    
    ## OPTIONAL ASPECTS TO CHECK
    {chr(10).join('- ' + o for o in optional_aspects)}
    
    ## AGENT MESSAGE
    {agent_message}
    
    ## CUSTOMER RESPONSE
    {customer_response}
    {context_section}
    
    IMPORTANT INSTRUCTIONS:
    - Be generous in your assessment - if there's reasonable evidence an aspect was fulfilled, count it as met
    - Optional aspects enhance the quality but are not required for progress
    - Consider intent rather than exact wording
    - Small typos or minor phrasing differences should not prevent recognizing a fulfilled aspect
    
    Return ONLY a JSON with one field:
    - "aspects_met": list of specific optional aspects that were met
    """
        
        try:
            print(f"Checking optional aspects in phase: {self.current_phase}")
            
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "You are a conversation evaluator focused on quality improvements. Be generous in your evaluation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0
            )
            
            result = response.choices[0].message.content.strip()
            print(f"Optional aspects raw response: {result}")
            
            import json
            try:
                # Clean JSON result from backticks and code markers
                cleaned_result = result
                if "```json" in cleaned_result:
                    cleaned_result = cleaned_result.replace("```json", "")
                if "```" in cleaned_result:
                    cleaned_result = cleaned_result.replace("```", "")
                cleaned_result = cleaned_result.strip()
                
                # Extract JSON if embedded in other text
                start_bracket = cleaned_result.find('{')
                end_bracket = cleaned_result.rfind('}')
                if start_bracket != -1 and end_bracket != -1:
                    cleaned_result = cleaned_result[start_bracket:end_bracket + 1]
                
                result_json = json.loads(cleaned_result)
                
                # Store fulfilled optional aspects
                fulfilled_aspects = result_json.get("aspects_met", [])
                if fulfilled_aspects:
                    print(f"Optional aspects fulfilled: {fulfilled_aspects}")
                    
                    # Avoid duplicates in the list
                    for aspect in fulfilled_aspects:
                        if aspect not in self.optional_aspects_fulfilled:
                            self.optional_aspects_fulfilled.append(aspect)
                            
                            # Actualizar contadores globales de aspectos opcionales
                            if aspect not in self.unique_optional_aspects:
                                self.unique_optional_aspects.add(aspect)
                                self.total_optional_aspects_count += 1
                
                return result_json
            except Exception as e:
                print(f"Error parsing JSON from optional aspects check: {result}")
                print(f"Specific error: {str(e)}")
                return {"aspects_met": []}
                
        except Exception as e:
            print(f"Error checking optional aspects: {str(e)}")
            return {"aspects_met": []}
            
    def _record_phase_transition(self, new_phase: str):
        """Records a phase transition."""
        if new_phase != self.current_phase:
            self.phase_history.append({
                "from": self.current_phase,
                "to": new_phase,
                "timestamp": time.time()
            })
            # When changing phase, reset the accumulated aspects for the new phase
            if new_phase not in self.cumulative_critical_aspects:
                self.cumulative_critical_aspects[new_phase] = []
            if new_phase not in self.cumulative_red_flags:
                self.cumulative_red_flags[new_phase] = []
            self.current_phase = new_phase

    def get_current_phase(self) -> str:
        return self.current_phase

    def get_system_prompt(self) -> str:
        return self.phase_config.get_phase(self.current_phase).system_prompt

    def get_phase_history(self) -> List[Dict]:
        return self.phase_history
    
    def is_closing_phase(self) -> bool:
        return self.current_phase.lower() in ["satisfied closure", "polite closure", "abrupt closure"]
    
    def update_phase(self, new_phase: str):
        self._record_phase_transition(new_phase)

    def get_optional_aspects_fulfilled(self) -> List[str]:
        """Returns the optional aspects fulfilled for feedback"""
        return self.optional_aspects_fulfilled
        
    def get_cumulative_critical_aspects(self, phase: str = None) -> List[str]:
        """Returns the accumulated critical aspects for a specific phase or the current one"""
        phase = phase or self.current_phase
        return self.cumulative_critical_aspects.get(phase, [])

    # Agregar métodos para obtener los contadores globales
    def get_total_critical_aspects_count(self) -> int:
        """Retorna el número total de aspectos críticos únicos detectados durante la conversación."""
        return self.total_critical_aspects_count

    def get_total_optional_aspects_count(self) -> int:
        """Retorna el número total de aspectos opcionales únicos detectados durante la conversación."""
        return self.total_optional_aspects_count

    def get_total_red_flags_count(self) -> int:
        """Retorna el número total de banderas rojas únicas detectadas durante la conversación."""
        return self.total_red_flags_count

    def get_aspect_counts(self) -> Dict:
        """Retorna un diccionario con todos los contadores de aspectos y banderas."""
        return {
            "critical_aspects": self.total_critical_aspects_count,
            "optional_aspects": self.total_optional_aspects_count,
            "red_flags": self.total_red_flags_count
        }


