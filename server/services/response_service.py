# server/services/response_service.py
"""
Service for generating conversation partner responses
"""
from .llm_manager import llm_manager
from .prompt_builder import PromptBuilder
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ResponseService:
    """
    Generates conversation partner responses (male persona)
    """
    
    def __init__(self):
        self.prompt_builder = PromptBuilder()
            # Import here to avoid circular imports
        from .conversation_service import ConversationService
        self.conversation_service = ConversationService()
    
    def generate_response(
        self,
        user_message: str,
        user_data: Dict,
        conversation_context: Dict,
        analysis: Dict
    ) -> Dict[str, str]:
        """
        Generate main conversation response
        """
        system_prompt, _ = self.prompt_builder.build_prompt(
            user_data,
            conversation_context,
            user_message,
            mode='chat'
        )
        
        # Add partner persona instruction
        system_prompt += """

You are the conversation partner (male persona).
Be friendly, patient, and encouraging.
Keep the conversation flowing naturally.
Ask questions to keep them engaged."""

        # If rephrase happened, acknowledge it subtly
        enhanced_message = user_message
        if analysis.get('needs_rephrase'):
            system_prompt += "\nThe student's response was just rephrased by the teacher. Continue naturally without mentioning it."

        response = llm_manager.generate_chat_response(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": enhanced_message}
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        return {
            'response': response.strip(),
            'continue_conversation': True
        }
    
    def generate_follow_up_after_teaching(
        self,
        user_data: Dict,
        conversation_context: Dict
    ) -> str:
        """
        Generate a follow-up after teaching explanation
        """
        learning_lang = user_data['learningLanguage']
        
        system_prompt = f"""You are a conversation partner (male persona) helping someone learn {learning_lang}.
The teacher just explained something to them.
Now continue the conversation naturally in {learning_lang}.

Rules:
1. Speak only in {learning_lang}
2. Reference what was just discussed if relevant
3. Ask an engaging question to continue
4. Be encouraging
5. Maximum 2 sentences"""

        response = llm_manager.generate_chat_response(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Continue the conversation after the explanation"}
            ],
            temperature=0.7,
            max_tokens=80
        )
        
        return response.strip()