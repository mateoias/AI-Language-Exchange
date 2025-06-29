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
from .parallel_orchestrator import ParallelOrchestrator  # PARALLEL: New import
from .error_detection_service import ErrorDetectionService
from .correction_strategy_service import CorrectionStrategyService

from flask import current_app
import json
import os
import logging  
logger = logging.getLogger(__name__) 

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
        self.intent_service = IntentService()
        self.rephrase_service = RephraseService()
        self.error_detection_service = ErrorDetectionService()
        self.correction_strategy_service = CorrectionStrategyService()
        self.response_service = ResponseService()
        self.parallel_orchestrator = None
    
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
        """Main method to generate chat response with parallel processing and error detection"""
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
            
            # NEW: Check if we should use parallel processing
            use_parallel = current_app.config.get('USE_PARALLEL_PROCESSING', True)
            
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
            
            # Step 2: ERROR DETECTION (NEW!)
            error_data = self.error_detection_service.detect_errors(
                message_content,
                conversation_context,
                user_data['learningLanguage']
            )
            
            logger.info(f"Error detection result: {error_data}")
            
            # Step 3: CORRECTION STRATEGY (NEW!)
            correction_settings = {
                'frequency': user_data.get('correctionFrequency', 50)  # From user settings
            }
            
            correction_strategy = self.correction_strategy_service.determine_correction_strategy(
                error_data,
                user_data,
                conversation_context,
                correction_settings
            )
            
            logger.info(f"Correction strategy: {correction_strategy['strategy']}")
            
            # Step 4: Determine if we need to rephrase (UPDATED!)
            # Now considers both errors and intent
            has_errors = error_data.get('has_errors', False)
            should_rephrase = rephrase_service.should_rephrase(
                user_data.get('proficiencyLevel', 'beginner'),
                has_errors,  # NOW USING ACTUAL ERROR DETECTION!
                intent_data['details']
            ) or correction_strategy.get('should_correct', False)
            
            # Add user message to conversation first
            self.conversation_service.add_message(
                user_id, message_content, 'user', intent_data['intent'], user_data['learningLanguage']
            )
            
            # NEW: Use parallel processing if enabled
            if use_parallel:
                # Initialize parallel orchestrator if needed
                if not self.parallel_orchestrator:
                    self.parallel_orchestrator = ParallelOrchestrator(
                        rephrase_service,
                        response_service,
                        self.audio_queue_service
                    )
                
                # Use parallel generation with error awareness
                result = self.parallel_orchestrator.generate_parallel_response_with_correction(
                    user_message=message_content,
                    user_data=user_data,
                    conversation_context=conversation_context,
                    intent_data=intent_data,
                    error_data=error_data,  # NEW!
                    correction_strategy=correction_strategy,  # NEW!
                    should_rephrase=should_rephrase,
                    audio_speed=audio_speed
                )
                
                segments_with_audio = result['segments']
                
                # Add bot response to conversation
                response_segment = next((s for s in segments_with_audio if s['type'] == 'response'), None)
                if response_segment:
                    self.conversation_service.add_message(
                        user_id, 
                        response_segment['text'], 
                        'bot', 
                        'chat', 
                        user_data['learningLanguage']
                    )
                
                return {
                    'segments': segments_with_audio,
                    'intent': intent_data['intent'],
                    'rephrased': should_rephrase,
                    'audio_language': user_data['learningLanguage'],
                    'generation_times': result.get('generation_times', {}),
                    'error_detected': has_errors,  # NEW!
                    'correction_applied': correction_strategy.get('should_correct', False)  # NEW!
                }
            
            else:
                # ORIGINAL CODE with error detection added
                segments = []
                
                # Generate correction/rephrase if needed
                if correction_strategy.get('should_correct') and correction_strategy.get('teacher_response'):
                    segments.append({
                        'type': 'correction',
                        'text': correction_strategy['teacher_response'],
                        'timing': 0,
                        'persona': 'teacher'
                    })
                elif should_rephrase and not correction_strategy.get('should_correct'):
                    # Regular rephrase (no error correction)
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
                            'timing': 0,
                            'persona': 'teacher' 
                        })
                
                # Generate main response with correction hint
                response_data = response_service.generate_response_with_correction_hint(
                    message_content,
                    user_data,
                    conversation_context,
                    intent_data,
                    correction_strategy.get('partner_hint', {})  # NEW!
                )
                
                # Add help segment if needed
                if response_data.get('help_text'):
                    segments.append({
                        'type': 'help',
                        'text': response_data['help_text'],
                        'timing': len(segments) * 800,
                        'persona': 'teacher' 
                    })
                
                # Add main response
                segments.append({
                    'type': 'response',
                    'text': response_data['response'],
                    'timing': len(segments) * 800,
                    'persona': 'partner'
                })
                
                # Generate audio for all segments
                segments_with_audio = self.audio_queue_service.generate_audio_segments(
                    segments,
                    user_data['learningLanguage'],
                    audio_speed,
                    user_data['nativeLanguage'] 
                )
                
                # Add bot response to conversation
                self.conversation_service.add_message(
                    user_id, 
                    response_data['response'], 
                    'bot', 
                    'chat', 
                    user_data['learningLanguage']
                )
                
                return {
                    'segments': segments_with_audio,
                    'intent': intent_data['intent'],
                    'rephrased': should_rephrase,
                    'audio_language': user_data['learningLanguage'],
                    'error_detected': has_errors,
                    'correction_applied': correction_strategy.get('should_correct', False)
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
        finally:
            # NEW: Cleanup parallel orchestrator if needed
            if hasattr(self, 'parallel_orchestrator') and self.parallel_orchestrator:
                try:
                    self.parallel_orchestrator.cleanup()
                except:
                    pass
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