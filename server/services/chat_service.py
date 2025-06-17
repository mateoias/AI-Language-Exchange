# services/chat_service.py
from ..models.conversation import Conversation, Message
from ..utils.file_utils import find_user_by_id
from .conversation_service import ConversationService
from .llm_manager import llm_manager
from .prompt_builder import PromptBuilder
from .audio_service import AudioService
from ..language_config import get_error_message

from flask import current_app
import json
import os

class ChatService:
    def __init__(self):
        self.conversation_service = ConversationService()
        self.prompt_builder = PromptBuilder()
        self.audio_service = AudioService()  # Use the dedicated audio service
    
    def detect_intent(self, message, user_native_language, user_learning_language):
        """
        Simple intent detection based on language.
        Target language = chat mode
        Native language = teaching mode
        """
        # Simple keyword detection for teaching mode
        teaching_keywords = [
            'what does', 'how do i', 'explain', 'grammar', 'why',
            'what is', 'help me understand', 'i don\'t understand'
        ]
        
        message_lower = message.lower()
        
        # Check for teaching keywords in any language
        for keyword in teaching_keywords:
            if keyword in message_lower:
                return 'teaching'
        
        # Default to chat mode
        return 'chat'
    
    def generate_response(self, user_id, message_content, audio_speed=0.8):
        """Main method to generate chat response with persistent memory and audio"""
        try:
            # Get user data
            user_data = find_user_by_id(user_id)
            if not user_data:
                raise ValueError("User not found")
            
            # Detect intent
            intent = self.detect_intent(
                message_content, 
                user_data['nativeLanguage'], 
                user_data['learningLanguage']
            )
            
            # For now, only handle chat mode
            if intent == 'teaching':
                # TODO: Route to teaching service
                response_text = f"I detected you need help! For now, I'll continue chatting in {user_data['learningLanguage']}. Teaching mode coming soon!"
                audio_data = self.audio_service.generate_audio(response_text, user_data['learningLanguage'], audio_speed)
                
                return {
                    'response': response_text,
                    'intent': 'teaching',
                    'audio_language': user_data['learningLanguage'],
                    'audio_data': audio_data
                }
            
            # Add user message to persistent conversation
            self.conversation_service.add_message(
                user_id, message_content, 'user', intent, user_data['learningLanguage']
            )
            
            # Get conversation context for prompt
            conversation_context = self.conversation_service.get_conversation_context(user_id)
            
            # Use PromptBuilder
            system_prompt, detected_level = self.prompt_builder.build_prompt(
                user_data,
                conversation_context,
                message_content,
                mode='chat'
            )
            
            # Use centralized LLM manager
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message_content}
            ]
            
            bot_response_content = llm_manager.generate_chat_response(
                messages=messages,
                temperature=0.3,
                max_tokens=150
            )
            
            # Generate audio using the audio service
            audio_data = self.audio_service.generate_audio(
                bot_response_content, 
                user_data['learningLanguage'],
                audio_speed
            )
            
            # Add bot response to persistent conversation
            self.conversation_service.add_message(
                user_id, bot_response_content, 'bot', 'chat', user_data['learningLanguage']
            )
            
            return {
                'response': bot_response_content,
                'intent': 'chat',
                'audio_language': user_data['learningLanguage'],
                'audio_data': audio_data,
                'level': detected_level
            }
            
        except Exception as e:
            # Graceful error handling
            error_message = get_error_message(user_data.get('learningLanguage', 'English') if user_data else 'English')
            audio_data = None
            
            if user_data:
                try:
                    audio_data = self.audio_service.generate_audio(
                        error_message, 
                        user_data.get('learningLanguage', 'English'),
                        audio_speed
                    )
                except:
                    pass
            
            return {
                'response': error_message,
                'intent': 'error',
                'audio_language': user_data.get('learningLanguage', 'English') if user_data else 'English',
                'audio_data': audio_data,
                'error': str(e)
            }
    
    def get_conversation_history(self, user_id):
        """Get conversation history using persistent storage"""
        return self.conversation_service.get_conversation_history(user_id)
    
    def start_new_session(self, user_id):
        """Start new conversation session"""
        # Clear audio cache in audio service
        self.audio_service.clear_cache()
        
        self.conversation_service.start_new_session(user_id)
        return {"message": "New session started"}