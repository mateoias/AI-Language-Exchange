# server/services/rephrase_service.py
"""
Service for rephrasing user responses into complete sentences
FIXED: Now uses proper conversation context
"""
from .llm_manager import llm_manager
import random
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class RephraseService:
    """
    Rephrases short user responses into complete sentences
    Handles error corrections when needed
    """
    
    def __init__(self):
        self.rephrase_templates = {
            'affirmative': {
                'spanish': [
                    "¡Sí, {context}!",
                    "Ah, entonces {context}.",
                    "¡Qué bien! {context}."
                ],
                'english': [
                    "Yes, {context}!",
                    "So {context}.",
                    "Great! {context}."
                ]
            },
            'negative': {
                'spanish': [
                    "No, no {context}.",
                    "Entonces no {context}.",
                    "Ah, no {context}."
                ],
                'english': [
                    "No, {context_negative}.",
                    "So you don't {context_negative}.",
                    "Ah, you don't {context_negative}."
                ]
            }
        }
    
    def should_rephrase(self, level: str, has_errors: bool, intent_details: Dict) -> bool:
        """
        Determine if we should rephrase based on level and context
        """
        if level == 'beginner':
            return intent_details.get('is_short', False) or has_errors
        elif level == 'intermediate':
            # Only for very short responses or errors
            return (has_errors or 
                    (intent_details.get('is_short', False) and 
                     len(intent_details.get('original_message', '').split()) <= 2))
        elif level == 'advanced':
            return has_errors
        return False
    
    def generate_rephrase(
        self, 
        user_message: str, 
        context: Dict,
        language: str,
        intent_details: Dict,
        errors: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Generate a rephrase of the user's message
        
        Args:
            user_message: Original user message
            context: Conversation context
            language: Target language
            intent_details: Details from intent detection
            errors: Any errors detected in the message
            
        Returns:
            Rephrased sentence or None
        """
        # Always use LLM for rephrasing to get context-aware responses
        return self._llm_rephrase(user_message, context, language, errors)
    
    def _llm_rephrase(
        self, 
        message: str, 
        context: Dict,
        language: str,
        errors: Optional[Dict] = None
    ) -> str:
        """Use LLM to generate rephrase with proper context"""
        
        # Get the last bot message for context
        last_bot_message = context.get('last_bot_message', '')
        recent_messages = context.get('recent_messages', [])
        
        # Build conversation context for the LLM
        conversation_context = ""
        if len(recent_messages) >= 2:
            # Get last 2-3 exchanges for context
            for i, msg in enumerate(recent_messages[-4:]):
                conversation_context += f"{msg['sender'].capitalize()}: {msg['content']}\n"
        
        system_prompt = f"""You are a language learning assistant helping students practice {language}.
Your task is to rephrase the student's response into a complete, grammatically correct sentence.

CRITICAL RULES:
1. You must understand the conversation context and respond appropriately
2. If the student gives a short answer to a question, expand it to answer that specific question
3. Keep it natural and conversational
4. Maintain the student's intended meaning
5. Keep it concise (under 15 words)
6. Respond ONLY with the rephrased sentence in {language}
7. Write from the teacher's perspective using second person (tú/usted)
   Example: Student says "nada" in response to "what are you doing?" → You write "No estás haciendo nada"
   NOT what the student would say: "No estoy haciendo nada"
8. IMPORTANT: Make sure your rephrase makes sense in the conversation context!

Examples of good rephrases:
- Question: "¿De qué te gustaría hablar?" Student: "de mi madre" → "Quieres hablar de tu madre"
- Question: "¿Qué has estado haciendo?" Student: "nada" → "No has estado haciendo nada"
- Question: "¿Cómo estás?" Student: "bien" → "Estás bien"
- Statement: "charlar" (in context of what to do) → "Quieres charlar"
"""

        user_prompt = f"""Recent conversation:
{conversation_context}

Current exchange:
Bot: {last_bot_message}
Student: "{message}"

Rephrase the student's response into a complete sentence that makes sense in this conversation context."""

        if errors:
            user_prompt += f"\nNote: The student made these errors: {errors.get('description', '')}"

        logger.debug(f"Rephrase prompt:\n{user_prompt}")

        response = llm_manager.generate_chat_response(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=50
        )
        
        result = response.strip()
        logger.info(f"Rephrased '{message}' to '{result}'")
        return result