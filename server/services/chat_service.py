# services/chat_service.py
from ..models.conversation import Conversation, Message
from ..utils.file_utils import find_user_by_id
from .conversation_service import ConversationService
from .llm_manager import llm_manager
from .prompt_builder import PromptBuilder
from .audio_service import AudioService
from .intent_service import IntentService
from .rephrase_service import RephraseService  
from .response_service import ResponseService
from .audio_queue_service import AudioQueueService
from ..language_config import get_error_message

from flask import current_app
import json
import os

class ChatService:
    def __init__(self, speech_key=None, speech_region=None):
        self.conversation_service = ConversationService()
        self.prompt_builder = PromptBuilder()
        self.speech_key = speech_key
        self.speech_region = speech_region
        # Only initialize audio services if credentials provided
        if speech_key and speech_region:
            self.audio_service = AudioService(speech_key, speech_region)
            self.audio_queue_service = AudioQueueService(speech_key, speech_region)
        else:
            self.audio_service = None
            self.audio_queue_service = None
    
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
        """Main method to generate chat response with parallel processing"""
        try:
            # Get user data
            user_data = find_user_by_id(user_id)
            if not user_data:
                raise ValueError("User not found")
            if not self.audio_service:
                self.audio_service = AudioService(self.speech_key, self.speech_region)
            if not self.audio_queue_service:
                self.audio_queue_service = AudioQueueService(self.speech_key, self.speech_region)
            
            # Initialize services
            intent_service = IntentService()
            rephrase_service = RephraseService()
            response_service = ResponseService()
            speech_key = current_app.config['AZURE_SPEECH_KEY']
            speech_region = current_app.config['AZURE_SPEECH_REGION']
            audio_queue_service = AudioQueueService(speech_key, speech_region)
            
            # Step 1: Quick intent detection
            intent_data = intent_service.detect_intent(
                message_content,
                user_data['learningLanguage']
            )
            
            # Get conversation context
            conversation_context = self.conversation_service.get_conversation_context(user_id)
            
            # Add context about last bot message
            recent_messages = conversation_context.get('recent_messages', [])
            if recent_messages:
                last_bot_msg = next((msg for msg in reversed(recent_messages) if msg['sender'] == 'bot'), None)
                if last_bot_msg:
                    conversation_context['last_bot_message'] = last_bot_msg['content']
            
            # Step 2: Determine if we need to rephrase
            # For now, assume no errors (error detection can be added later)
            has_errors = False
            should_rephrase = rephrase_service.should_rephrase(
                user_data.get('proficiencyLevel', 'beginner'),
                has_errors,
                intent_data['details']
            )
            
            # Step 3: Build response segments
            segments = []
            
            # Add user message to conversation first
            self.conversation_service.add_message(
                user_id, message_content, 'user', intent_data['intent'], user_data['learningLanguage']
            )
            
            # Generate rephrase if needed
            if should_rephrase:
                rephrase_text = rephrase_service.generate_rephrase(
                    message_content,
                    conversation_context,
                    user_data['learningLanguage'],
                    intent_data['details']
                )
                if rephrase_text:
                    segments.append({
                        'type': 'rephrase',
                        'text': rephrase_text,
                        'timing': 0
                    })
            
            # Generate main response (with optional help)
            response_data = response_service.generate_response(
                message_content,
                user_data,
                conversation_context,
                intent_data
            )
            
            # Add help segment if needed
            if response_data.get('help_text'):
                segments.append({
                    'type': 'help',
                    'text': response_data['help_text'],
                    'timing': len(segments) * 800  # 2 seconds per segment
                })
            
            # Add main response
            segments.append({
                'type': 'response',
                'text': response_data['response'],
                'timing': len(segments) * 800
            })
            
            # Step 4: Generate audio for all segments in parallel
            segments_with_audio = audio_queue_service.generate_audio_segments(
                segments,
                user_data['learningLanguage'],
                audio_speed
            )
            
            # Add bot response to conversation
            self.conversation_service.add_message(
                user_id, 
                response_data['response'], 
                'bot', 
                'chat', 
                user_data['learningLanguage']
            )
            
            # Cleanup
            audio_queue_service.cleanup()
            
            return {
                'segments': segments_with_audio,
                'intent': intent_data['intent'],
                'rephrased': should_rephrase,
                'audio_language': user_data['learningLanguage']
            }
            
        except Exception as e:
            # Error handling remains the same
            error_message = get_error_message(user_data.get('learningLanguage', 'English') if user_data else 'English')
            return {
                'segments': [{
                    'type': 'error',
                    'text': error_message,
                    'audio_data': None,
                    'timing': 0
                }],
                'intent': 'error',
                'audio_language': user_data.get('learningLanguage', 'English') if user_data else 'English',
                'error': str(e)
            }


    def get_conversation_history(self, user_id):
        """Get conversation history using persistent storage"""
        return self.conversation_service.get_conversation_history(user_id)
    
    def start_new_session(self, user_id):
        """Start new conversation session"""
        # Finalize current conversation first
        finalized_data = self.conversation_service.finalize_conversation(user_id)
        if finalized_data:
            print(f"Conversation {finalized_data['conversation_id']} finalized with {finalized_data['message_count']} messages")
            # TODO: Queue for database storage
        
        # Clear audio cache in audio service
        self.audio_service.clear_cache()
        
        # Start new conversation
        self.conversation_service.start_new_session(user_id)
        return {"message": "New session started", "previous_conversation_finalized": bool(finalized_data)}