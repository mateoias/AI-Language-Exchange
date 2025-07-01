# server/services/chat_service.py
"""
Simplified ChatService that orchestrates the conversation flow
"""
from ..models.conversation import Message
from ..utils.file_utils import find_user_by_id
from .conversation_service import ConversationService
from .llm_manager import llm_manager
from .prompt_builder import PromptBuilder
from .audio_service import AudioService
from .audio_queue_service import AudioQueueService
from .conversation_analysis_service import ConversationAnalysisService
from .teaching_service import TeachingService
from .response_service import ResponseService
from .parallel_orchestrator import ParallelOrchestrator
from ..language_config import get_error_message
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, speech_key=None, speech_region=None):
        self.conversation_service = ConversationService()
        self.prompt_builder = PromptBuilder()
        self.analysis_service = ConversationAnalysisService()
        self.teaching_service = TeachingService()
        self.response_service = ResponseService()
        
        # Audio services
        if speech_key and speech_region:
            self.audio_service = AudioService(speech_key, speech_region)
            self.audio_queue_service = AudioQueueService(speech_key, speech_region)
            self.parallel_orchestrator = ParallelOrchestrator(
                self.teaching_service,
                self.response_service,
                self.audio_queue_service
            )
        else:
            self.audio_service = None
            self.audio_queue_service = None
            self.parallel_orchestrator = None
    
    def generate_response(self, user_id, message_content, audio_speed=0.8):
        """Main entry point for generating chat responses"""
        try:
            # Get user data
            user_data = find_user_by_id(user_id)
            if not user_data:
                raise ValueError("User not found")
            
            # Get conversation context
            conversation_context = self.conversation_service.get_conversation_context(user_id)
            
            # Add last bot message to context
            recent_messages = conversation_context.get('recent_messages', [])
            if recent_messages:
                last_bot_msg = next(
                    (msg for msg in reversed(recent_messages) if msg['sender'] == 'bot'), 
                    None
                )
                if last_bot_msg:
                    conversation_context['last_bot_message'] = last_bot_msg['content']
            
            # Analyze the message to determine flow
            analysis = self.analysis_service.analyze_message(
                message_content, 
                user_data, 
                conversation_context
            )
            
            logger.info(f"Analysis result: {analysis}")
            
            # Add user message to conversation
            self.conversation_service.add_message(
                user_id, message_content, 'user', 'chat', user_data['learningLanguage']
            )
            
            # Route to appropriate handler
            if analysis['flow_type'] == 'teaching':
                return self._handle_teaching_flow(
                    analysis, user_data, conversation_context, audio_speed
                )
            elif analysis['flow_type'] == 'repair':
                return self._handle_repair_flow(
                    message_content, analysis, user_data, conversation_context, audio_speed
                )
            else:  # normal conversation
                return self._handle_conversation_flow(
                    message_content, analysis, user_data, conversation_context, audio_speed
                )
            
        except Exception as e:
            logger.error(f"Chat service error: {e}")
            return self._error_response(user_data, str(e))
    
    def _handle_teaching_flow(
        self, analysis, user_data, conversation_context, audio_speed
    ):
        """Handle direct teaching requests (explanations in native language)"""
        segments = []
        
        # Generate explanation
        explanation = self.teaching_service.generate_explanation(
            analysis['teaching_request'],
            user_data,
            conversation_context
        )
        
        segments.append({
            'type': 'help',
            'text': explanation,
            'timing': 0,
            'persona': 'teacher'
        })
        
        # Continue conversation with a follow-up
        follow_up = self.response_service.generate_follow_up_after_teaching(
            user_data,
            conversation_context
        )
        
        segments.append({
            'type': 'response',
            'text': follow_up,
            'timing': 800,
            'persona': 'partner'
        })
        
        # Generate audio
        segments_with_audio = self.audio_queue_service.generate_audio_segments(
            segments,
            user_data['learningLanguage'],
            audio_speed,
            user_data['nativeLanguage']
        )
        
        # Add follow-up to conversation history
        self.conversation_service.add_message(
            user_data['id'], follow_up, 'bot', 'chat', user_data['learningLanguage']
        )
        
        return {
            'segments': segments_with_audio,
            'intent': 'teaching',
            'audio_language': user_data['learningLanguage']
        }
    
    def _handle_repair_flow(
        self, message_content, analysis, user_data, conversation_context, audio_speed
    ):
        """Handle conversation repair (wrong language, unclear, etc)"""
        segments = []
        
        # Generate repair response
        repair_text = self.teaching_service.generate_repair(
            message_content,
            analysis['repair_type'],
            user_data,
            conversation_context
        )
        
        segments.append({
            'type': 'correction',
            'text': repair_text,
            'timing': 0,
            'persona': 'teacher'
        })
        
        # Generate audio
        segments_with_audio = self.audio_queue_service.generate_audio_segments(
            segments,
            user_data['learningLanguage'],
            audio_speed
        )
        
        # Add to conversation
        self.conversation_service.add_message(
            user_data['id'], repair_text, 'bot', 'repair', user_data['learningLanguage']
        )
        
        return {
            'segments': segments_with_audio,
            'intent': 'repair',
            'audio_language': user_data['learningLanguage']
        }
    
    def _handle_conversation_flow(
        self, message_content, analysis, user_data, conversation_context, audio_speed
    ):
        """Handle normal conversation with optional rephrasing"""
        
        # Use parallel processing if available
        use_parallel = (
            current_app.config.get('USE_PARALLEL_PROCESSING', True) and 
            self.parallel_orchestrator is not None
        )
        
        if use_parallel and (analysis['needs_rephrase'] or 
                           user_data.get('proficiencyLevel') == 'beginner'):
            # Use parallel generation for perceived speed
            return self.parallel_orchestrator.generate_parallel_response(
                message_content,
                user_data,
                conversation_context,
                analysis,
                audio_speed
            )
        else:
            # Sequential generation for simpler cases
            segments = []
            
            # Rephrase if needed
            if analysis['needs_rephrase']:
                rephrase_text = self.teaching_service.generate_rephrase(
                    message_content,
                    conversation_context,
                    user_data['learningLanguage'],
                    user_data.get('proficiencyLevel', 'beginner')
                )
                if rephrase_text:
                    segments.append({
                        'type': 'rephrase',
                        'text': rephrase_text,
                        'timing': 0,
                        'persona': 'teacher'
                    })
            
            # Generate main response
            response_data = self.response_service.generate_response(
                message_content,
                user_data,
                conversation_context,
                analysis
            )
            
            segments.append({
                'type': 'response',
                'text': response_data['response'],
                'timing': len(segments) * 800,
                'persona': 'partner'
            })
            
            # Generate audio
            segments_with_audio = self.audio_queue_service.generate_audio_segments(
                segments,
                user_data['learningLanguage'],
                audio_speed,
                user_data['nativeLanguage']
            )
            
            # Add to conversation
            self.conversation_service.add_message(
                user_data['id'], 
                response_data['response'], 
                'bot', 
                'chat', 
                user_data['learningLanguage']
            )
            
            return {
                'segments': segments_with_audio,
                'intent': 'chat',
                'rephrased': analysis['needs_rephrase'],
                'audio_language': user_data['learningLanguage']
            }
    
    def _error_response(self, user_data, error_msg):
        """Generate error response"""
        error_message = get_error_message(
            user_data.get('learningLanguage', 'English') if user_data else 'English'
        )
        return {
            'segments': [{
                'type': 'error',
                'text': error_message,
                'audio_data': None,
                'timing': 0
            }],
            'intent': 'error',
            'audio_language': user_data.get('learningLanguage', 'English') if user_data else 'English',
            'error': error_msg
        }
    
    def get_conversation_history(self, user_id):
        """Get conversation history"""
        return self.conversation_service.get_conversation_history(user_id)
    
    def start_new_session(self, user_id):
        """Start new conversation session"""
        finalized_data = self.conversation_service.finalize_conversation(user_id)
        if finalized_data:
            logger.info(f"Finalized conversation {finalized_data['conversation_id']}")
        
        if self.audio_service:
            self.audio_service.clear_cache()
        
        self.conversation_service.start_new_session(user_id)
        return {
            "message": "New session started", 
            "previous_conversation_finalized": bool(finalized_data)
        }