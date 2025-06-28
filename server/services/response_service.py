# server/services/response_service.py
# ENHANCED VERSION - New methods for parallel generation

from .llm_manager import llm_manager
from .prompt_builder import PromptBuilder
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ResponseService:
    """
    Generates the main conversational response
    Can include help/explanations based on intent
    Enhanced to support parallel generation with hints
    """
    
    def __init__(self):
        self.prompt_builder = PromptBuilder()
    
    def generate_response(
        self,
        user_message: str,
        user_data: Dict,
        conversation_context: Dict,
        intent_data: Dict,
        include_help: bool = False,
        rephrase_text: Optional[str] = None 
    ) -> Dict[str, str]:
        """
        Generate the main conversation response
        
        Returns:
            {
                'response': str,
                'help_text': Optional[str],
                'continue_conversation': bool
            }
        """
        # Build the appropriate prompt based on intent
        if intent_data['intent'] == 'help_needed':
            return self._generate_help_response(
                user_message, 
                user_data, 
                conversation_context,
                intent_data,
                rephrase_text
            )
        else:
            return self._generate_chat_response(
                user_message,
                user_data,
                conversation_context,
                rephrase_text
            )
    
    def generate_response_with_hint(
        self,
        user_message: str,
        user_data: Dict,
        conversation_context: Dict,
        hint: Dict,
        rephrase_text: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate response with a hint about likely corrections
        This allows the partner to naturally incorporate corrections
        """
        system_prompt, _ = self.prompt_builder.build_prompt(
            user_data,
            conversation_context,
            user_message,
            mode='chat'
        )
        
        # Add special instructions for natural correction handling
        enhanced_prompt = f"""{system_prompt}

IMPORTANT: The student's response might be incomplete or have minor errors.
Based on context, they likely mean: {hint.get('likely_meaning', 'continuation of conversation')}.
Respond naturally as if they said it correctly, without pointing out any errors.
If they gave a short response, expand on it conversationally."""

        # Construct the effective message with context
        if hint.get('is_short') and hint.get('response_type'):
            # For short responses, provide context
            effective_message = f"""The student said: "{user_message}"
Context: This appears to be a {hint['response_type']} response to your previous question.
Continue the conversation naturally."""
        else:
            effective_message = user_message

        response = llm_manager.generate_chat_response(
            messages=[
                {"role": "system", "content": enhanced_prompt},
                {"role": "user", "content": effective_message}
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        return {
            'response': response,
            'help_text': None,
            'continue_conversation': True
        }
    
    def _generate_chat_response(
        self,
        user_message: str,
        user_data: Dict,
        conversation_context: Dict,
        rephrase_text: Optional[str] = None
    ) -> Dict[str, str]:
        """Generate normal chat response"""
        system_prompt, _ = self.prompt_builder.build_prompt(
            user_data,
            conversation_context,
            user_message,
            mode='chat'
        )
        
        # ENHANCED: Handle rephrase more naturally
        if rephrase_text:
            # Don't explicitly mention the rephrase
            effective_message = user_message
            # Add subtle context to the system prompt
            system_prompt += f"\nNote: The student is practicing expressing themselves. Respond to their intent naturally."
        else:
            effective_message = user_message

        response = llm_manager.generate_chat_response(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": effective_message}
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        return {
            'response': response,
            'help_text': None,
            'continue_conversation': True
        }
    
# Replace the _generate_help_text method in your response_service.py with this:

    def _generate_help_text(
        self,
        user_message: str,
        user_data: Dict,
        help_type: str,
        conversation_context: Optional[Dict] = None
    ) -> str:
        """Generate specific help text with context awareness"""
        native_lang = user_data['nativeLanguage']
        learning_lang = user_data['learningLanguage']
        
        # Extract the phrase they're asking about
        import re
        # Pattern to match quoted text or text after "mean" or "significa"
        quote_pattern = r'"([^"]*)"'
        match = re.search(quote_pattern, user_message)
        phrase_to_explain = match.group(1) if match else user_message
        
        if help_type == 'translation':
            prompt = f"""Translate this phrase from {learning_lang} to {native_lang}.
Be accurate and natural. If it's a sentence fragment, translate it as such.
Provide ONLY the translation, no explanations.

Phrase: {phrase_to_explain}"""
        
        elif help_type == 'explanation':
            # For "what does X mean" questions
            prompt = f"""The student is learning {learning_lang} and asked what this means.
Explain in simple {native_lang} what this phrase means.
Be brief and clear (1-2 sentences max).
If the phrase seems incomplete or strange, mention that too.

Phrase to explain: "{phrase_to_explain}"

Provide a natural explanation as you would to a language learner."""
        
        else:  # general help
            prompt = f"""The student learning {learning_lang} seems confused.
They said: "{user_message}"
Provide a brief helpful response in {native_lang}."""
        
        response = llm_manager.generate_chat_response(
            messages=[
                {"role": "system", "content": f"You are a helpful {learning_lang} language tutor. Always be accurate and helpful."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=100
        )
        
        return response.strip()