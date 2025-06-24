# server/services/response_service.py
"""
Service for generating main conversation responses
"""
from .llm_manager import llm_manager
from .prompt_builder import PromptBuilder
from typing import Dict, Optional

class ResponseService:
    """
    Generates the main conversational response
    Can include help/explanations based on intent
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
    
    def _generate_help_response(
        self,
        user_message: str,
        user_data: Dict,
        conversation_context: Dict,
        intent_data: Dict,
        rephrase_text: Optional[str] = None
    ) -> Dict[str, str]:
        """Generate response when help is needed"""
        help_type = intent_data['details']['help_type']
        
        # Generate help content
        help_text = self._generate_help_text(
            user_message,
            user_data,
            help_type
        )
        
        # Generate continuation prompt
        system_prompt, _ = self.prompt_builder.build_prompt(
            user_data,
            conversation_context,
            user_message,
            mode='chat'
        )
        
        continuation_prompt = f"""{system_prompt}

The student just asked for help. I've provided the help.
Now continue the conversation naturally, acknowledging they needed help but moving forward.
Keep it encouraging and simple."""

        continuation = llm_manager.generate_chat_response(
            messages=[
                {"role": "system", "content": continuation_prompt},
                {"role": "user", "content": f"I just helped them with: {help_text[:100]}..."}
            ],
            temperature=0.5,
            max_tokens=100
        )
        
        return {
            'response': continuation,
            'help_text': help_text,
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
        if rephrase_text:
        # Add context about the rephrase
            effective_message = f"The student said '{user_message}' which means '{rephrase_text}'. Acknowledge this naturally and continue the conversation."
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
        
        response = llm_manager.generate_chat_response(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        return {
            'response': response,
            'help_text': None,
            'continue_conversation': True
        }
    
    def _generate_help_text(
        self,
        user_message: str,
        user_data: Dict,
        help_type: str
    ) -> str:
        """Generate specific help text"""
        native_lang = user_data['nativeLanguage']
        learning_lang = user_data['learningLanguage']
        
        if help_type == 'translation':
            prompt = f"""Translate this phrase from {learning_lang} to {native_lang}.
Provide ONLY the translation, no explanations.

Phrase: {user_message}"""
        
        elif help_type == 'explanation':
            prompt = f"""Explain what this means in simple {native_lang}.
Keep it brief (1-2 sentences).

Phrase: {user_message}"""
        
        else:  # general help
            prompt = f"""The student learning {learning_lang} seems confused.
Provide a brief helpful hint in {native_lang} about: {user_message}"""
        
        response = llm_manager.generate_chat_response(
            messages=[
                {"role": "system", "content": "You are a helpful language tutor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=100
        )
        
        return response.strip()