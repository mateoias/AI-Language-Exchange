# server/services/rephrase_service.py
"""
Service for rephrasing user responses into complete sentences
"""
from .llm_manager import llm_manager
import random
from typing import Dict, Optional

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
            return True
        elif level == 'intermediate':
            # 50% chance for normal responses, always for errors or short responses
            return has_errors or intent_details.get('is_short', False) or random.random() > 0.5
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
        # For very short responses, try template-based approach first
        if intent_details.get('is_short') and intent_details.get('response_type'):
            template_rephrase = self._try_template_rephrase(
                user_message, 
                intent_details['response_type'],
                context,
                language
            )
            if template_rephrase:
                return template_rephrase
        
        # Fall back to LLM for complex rephrasing
        return self._llm_rephrase(user_message, context, language, errors)
    
    def _try_template_rephrase(
        self, 
        message: str, 
        response_type: str,
        context: Dict,
        language: str
    ) -> Optional[str]:
        """Try to use a template for common short responses"""
        templates = self.rephrase_templates.get(response_type, {}).get(language.lower(), [])
        
        if not templates:
            return None
        
        # Extract context from recent conversation
        last_bot_message = context.get('last_bot_message', '')
        topic = context.get('current_topic', '')
        
        # Simple context extraction (this could be enhanced)
        context_phrase = self._extract_context_phrase(last_bot_message, language)
        
        if context_phrase:
            template = random.choice(templates)
            return template.format(
                context=context_phrase,
                context_negative=f"don't {context_phrase}" if language == 'english' else f"no {context_phrase}"
            )
        
        return None
    
    def _extract_context_phrase(self, last_message: str, language: str) -> str:
        """Extract a simple context phrase from the last bot message"""
        # This is a simplified version - could be enhanced with NLP
        if '?' in last_message:
            # Try to extract the subject of the question
            question_part = last_message.split('?')[0]
            
            # Look for common patterns
            if language.lower() == 'spanish':
                if 'te gusta' in question_part.lower():
                    return 'te gusta'
                elif 'tienes' in question_part.lower():
                    return 'tienes'
            elif language.lower() == 'english':
                if 'do you like' in question_part.lower():
                    return 'you like that'
                elif 'do you have' in question_part.lower():
                    return 'you have that'
        
        return ""
    
    def _llm_rephrase(
        self, 
        message: str, 
        context: Dict,
        language: str,
        errors: Optional[Dict] = None
    ) -> str:
        """Use LLM to generate rephrase"""
        system_prompt = f"""You are a language learning assistant helping students practice {language}.
Your task is to rephrase the student's response into a complete, grammatically correct sentence.

Rules:
1. Keep it natural and conversational
2. If there are errors, correct them naturally without pointing them out
3. Maintain the student's intended meaning
4. Keep it concise (under 15 words)
5. Use the conversation context to fill in missing information
6. Respond ONLY with the rephrased sentence in {language}
7. IMPORTANT: Write from your perspective using second person (you/your/yours)
   Example: Student says "soccer" → You write "you like soccer" 
   NOT what the student would say: I like soccer"""

        user_prompt = f"""Student said: "{message}"

Context: The last thing said was: "{context.get('last_bot_message', '')}"

Rephrase this into a complete sentence in {language}."""

        if errors:
            user_prompt += f"\nNote: The student made these errors: {errors.get('description', '')}"

        response = llm_manager.generate_chat_response(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=50
        )
        
        return response.strip()