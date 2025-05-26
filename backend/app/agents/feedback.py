from app.services.azure_openai import AzureOpenAIClient
from typing import Dict, List, Any
from app.services.supabase import SupabasePhasesService

class FeedbackAgent:
    def __init__(self):
        self.llm = AzureOpenAIClient()
        self.supabase = SupabasePhasesService()
        assert self.supabase.initialize(), "Could not initialize Supabase client"

    def analyze_optional_conditions(self, conversation_history: List[Dict[str, Any]]) -> List[str]:
        """
        Analyzes the conversation history to determine which optional conditions were met.
        
        Args:
            conversation_history (List[Dict[str, Any]]): List of conversation messages as dictionaries
        
        Returns:
            List[str]: List of met optional condition descriptions
        """
        # Get optional conditions from database
        optional_conditions = self.supabase.get_optional_conditions()
        
        if not optional_conditions:
            return []

        # Create prompt for LLM
        conditions_text = "\n".join([f"{i+1}. {cond['description']}" for i, cond in enumerate(optional_conditions)])
        # Extraer solo el contenido de los mensajes
        conversation_text = "\n".join([msg.get("content", "") for msg in conversation_history])
        
        prompt = f"""
        Analyze the following conversation and determine which of these optional conditions were met.
        Only return conditions that are CLEARLY demonstrated in the conversation.
        
        Optional Conditions:
        {conditions_text}
        
        Conversation:
        {conversation_text}
        
        Return ONLY a comma-separated list of numbers corresponding to the conditions that were met.
        For example: "1,3,4" or "none" if no conditions were met.
        """
        
        try:
            response = self.llm.get_response(
                system_prompt="You are an objective conversation analyzer. Return ONLY comma-separated numbers or 'none'.",
                user_prompt=prompt
            )
            
            if response.lower().strip() == "none":
                return []
                
            # Convert response to list of met conditions
            try:
                met_indices = [int(idx.strip()) - 1 for idx in response.split(",")]
                met_conditions = [optional_conditions[idx]["description"] for idx in met_indices if idx < len(optional_conditions)]
                return met_conditions
            except (ValueError, IndexError) as e:
                print(f"[ERROR] Error al procesar la respuesta del LLM: {e}")
                return []
            
        except Exception as e:
            print(f"[ERROR] Error al analizar condiciones opcionales: {e}")
            return []

    def calculate_custom_score(self, accumulated_conditions: List[str], conditions: List[str], optional_aspects: List[str], red_flags: List[str]) -> Dict[str, any]:
        """
        Calcula un score personalizado basado en las condiciones acumuladas vs totales.
        
        La fórmula es:
        - Score base: 0 puntos
        - Cada condición cumplida: +20 puntos
        - Cada aspecto opcional: +10 puntos
        - Cada red flag: -40 puntos
        
        El resultado se normaliza a una escala 0-100.
        """
        # Cálculo basado en condiciones cumplidas
        base_score = 0
        condition_points = 20  # puntos por condición cumplida
        optional_points = 10  # puntos por aspecto opcional
        red_flag_penalty = 40  # puntos deducidos por red flag
        
        # Calcular cada componente usando la longitud de las listas
        conditions_bonus = len(accumulated_conditions) * condition_points
        optional_bonus = len(optional_aspects) * optional_points
        penalty = len(red_flags) * red_flag_penalty
        
        # Cálculo del score final (en escala según máximo posible)
        raw_score = base_score + conditions_bonus + optional_bonus - penalty
        
        # Asegurar que el score no sea negativo
        raw_score = max(0, raw_score)
        
        # Normalizar a escala 0-100 (máximo teórico es conditions_totales * condition_points)
        max_theoretical_score = len(conditions) * condition_points
        normalized_score = round((raw_score / max_theoretical_score) * 100) if max_theoretical_score > 0 else 0
        
        # Detalles del cálculo para explicación
        score_details = {
            "base_score": base_score,
            "conditions_bonus": conditions_bonus,
            "optional_bonus": optional_bonus,
            "red_flags_penalty": -penalty,
            "raw_score": raw_score,
            "normalized_score": normalized_score,
            "red_flags": red_flags,
            "optional_aspects": optional_aspects
        }
        
        # Explicación textual del cálculo
        explanation = (
            f"Base score: {base_score}\n"
            f"Condiciones cumplidas: +{conditions_bonus} ({len(accumulated_conditions)} × {condition_points} puntos)\n"
            f"Aspectos opcionales: +{optional_bonus} ({len(optional_aspects)} × {optional_points} puntos)\n"
            f"Red flags: -{penalty} ({len(red_flags)} × {red_flag_penalty} puntos)\n"
            f"Score bruto: {raw_score} (escala 0-{max_theoretical_score})\n"
            f"Score normalizado: {normalized_score}/100"
        )

        return {
            "score": normalized_score,
            "details": score_details,
            "explanation": explanation,
            "aspect_counts": {
                "total_conditions": len(conditions),
                "achieved_conditions": len(accumulated_conditions),
                "optional_aspects": len(optional_aspects),
                "red_flags": len(red_flags)
            }
        }

    def generate_feedback_prompt(self, conversation_history, conditions, accumulated_conditions=None):
        return f"""
        You are a feedback agent that evaluates the conversation history and gives feedback to the user.
        The conversation history is:
        {conversation_history}
        All the conditions that could be achieved are:
        {conditions}
        The conditions that have been achieved are:
        {accumulated_conditions}

        Your task is to give feedback to the user based on the conversation history and the conditions, with the following format as a JSON object:
        The custom score is the sum of the metrics, the custom score explanation is a short explanation of the custom score, the score details is a dictionary of the score details, the aspect counts is a dictionary of the aspect counts, the suggestions is a list of suggestions, the strength is a list of strengths, the opportunity is a list of opportunities, the issues is a list of issues.
        {{
          "metrics": {{"clarity": 4, "empathy": 5}},
          "custom_score": 87,
          "custom_score_explanation": "Great job! You showed empathy and clarity.",
          "score_details": {{}},
          "aspect_counts": {{"critical": 2, "optional": 1, "red_flags": 0}},
          "suggestions": [
            "Try to ask more open-ended questions.",
            "Summarize the customer's needs at the end."
          ],
          "strength": [
            "You were empathetic.",
            "You explained the features clearly."
          ],
          "opportunity": [
            "Could improve on handling objections."
          ],
          "issues": [
            "Missed an opportunity to upsell."
          ]
        }}

        Return ONLY a valid JSON object in this format.
        """

    def generate_feedback(self, conversation_history, conditions, accumulated_conditions, optional_aspects=None, red_flags=None):
        # Inicializar listas vacías si no se proporcionan
        optional_aspects = optional_aspects if optional_aspects is not None else []
        red_flags = red_flags if red_flags is not None else []
        
        # Calcular el score personalizado
        score_data = self.calculate_custom_score(accumulated_conditions, conditions, optional_aspects, red_flags)
        
        # Generar el feedback usando el LLM
        prompt = self.generate_feedback_prompt(conversation_history, conditions, accumulated_conditions)
        llm_response = self.llm.get_response(
            system_prompt="You are a feedback agent that evaluates conversations and provides structured feedback.",
            user_prompt=prompt
        )
        
        # Convertir la respuesta del LLM a diccionario
        import json
        feedback_dict = json.loads(llm_response)
        
        # Crear el formato final que espera el frontend
        return {
            "metrics": feedback_dict.get("metrics", {"clarity": 4, "empathy": 4}),
            "custom_score": score_data["score"],
            "custom_score_explanation": score_data["explanation"].replace("\n", " "),
            "score_details": score_data["details"],
            "aspect_counts": {
                "critical": len(accumulated_conditions),
                "optional": len(optional_aspects),
                "red_flags": len(red_flags)
            },
            "suggestions": feedback_dict.get("suggestions", [
                "Consider asking more follow-up questions.",
                "Try to provide more specific examples."
            ]),
            "strength": feedback_dict.get("strength", [
                "Good communication skills.",
                "Professional approach."
            ]),
            "opportunity": feedback_dict.get("opportunity", [
                "Could improve engagement with more detailed responses."
            ]),
            "issues": feedback_dict.get("issues", [
                "Some key points could have been addressed more thoroughly."
            ])
        }
