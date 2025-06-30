# server/services/unified_chat_service.py
"""
Unified Chat Service - Single LLM call for all analysis and response generation
Reduces latency and complexity while maintaining all functionality
"""
from typing import Dict, List, Optional, Tuple
import json
import logging
import time
from .llm_manager import llm_manager
from .audio_queue_service import AudioQueueService
from .prompt_builder import PromptBuilder
from ..language_config import get_error_message

logger = logging.getLogger(__name__)

class UnifiedChatService:
    """
    Unified service that handles everything in a single LLM call:
    - Intent detection
    - Error analysis
    - Correction generation
    - Conversation response
    """
    
    def __init__(self, speech_key=None, speech_region=None):
        self.prompt_builder = PromptBuilder()
        self.audio_queue_service = AudioQueueService(speech_key, speech_region) if speech_key else None
    
    def generate_response(
        self, 
        user_id: str, 
        message_content: str, 
        audio_speed: float = 0.8
    ) -> Dict:
        """
        Generate complete response with all analysis in one LLM call
        """
        try:
            # Get user data
            from ..utils.file_utils import find_user_by_id
            user_data = find_user_by_id(user_id)
            if not user_data:
                raise ValueError("User not found")
            
            # Get conversation context
            from .conversation_service import ConversationService
            conv_service = ConversationService()
            conversation_context = conv_service.get_conversation_context(user_id)
            
            # Build unified prompt
            unified_prompt = self._build_unified_prompt(
                user_data, 
                message_content, 
                conversation_context
            )
            
            # Single LLM call for everything
            start_time = time.time()
            response = llm_manager.generate_chat_response(
                messages=[
                    {"role": "system", "content": unified_prompt},
                    {"role": "user", "content": message_content}
                ],
                temperature=0.7,
                max_tokens=300,
                log_request=True
            )
            llm_time = (time.time() - start_time) * 1000
            
            # Parse structured response
            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM response: {response}")
                result = self._get_fallback_response(message_content, user_data)
            
            # Build segments from result
            segments = self._build_segments_from_result(result, user_data)
            
            # Generate audio if available
            if self.audio_queue_service:
                segments = self.audio_queue_service.generate_audio_segments(
                    segments,
                    user_data['learningLanguage'],
                    audio_speed,
                    user_data['nativeLanguage']
                )
            
            # Add bot response to conversation
            main_response = next((s for s in segments if s['type'] == 'response'), None)
            if main_response:
                conv_service.add_message(
                    user_id, 
                    main_response['text'], 
                    'bot', 
                    result.get('intent', 'chat'),
                    user_data['learningLanguage']
                )
            
            return {
                'segments': segments,
                'intent': result.get('intent', 'chat'),
                'audio_language': user_data['learningLanguage'],
                'performance': {
                    'llm_time_ms': llm_time,
                    'total_segments': len(segments)
                }
            }
            
        except Exception as e:
            logger.error(f"Unified response generation failed: {e}")
            return self._get_error_response(user_data, str(e))
    
    def _build_unified_prompt(
        self, 
        user_data: Dict, 
        message: str,
        conversation_context: Dict
    ) -> str:
        """
        Build a single prompt that handles all analysis and generation
        """
        level = user_data.get('proficiencyLevel', 'beginner').lower()
        language = user_data['learningLanguage']
        native_lang = user_data['nativeLanguage']
        
        # Get recent messages for context
        recent_messages = conversation_context.get('recent_messages', [])[-6:]
        context_str = self._format_conversation_context(recent_messages)
        
        # Get personalization preview (will be expanded with Neo4j)
        personalization = self._get_personalization_context(user_data)
        
        # Build the unified prompt
        prompt = f"""You are a language learning system with two personas:
1. TEACHER: Helps with corrections and explanations (in {native_lang} or {language})
2. PARTNER: Continues natural conversation (in {language})

USER PROFILE:
- Name: {user_data.get('username', 'Student')}
- Level: {level}
- Learning: {language}
- Native: {native_lang}
{personalization}

RECENT CONVERSATION:
{context_str}

CURRENT MESSAGE: [User says] "{message}"

ANALYZE AND RESPOND:
1. Detect if the message needs help (wrong language, asking for translation/explanation)
2. Generate appropriate response segments

RESPONSE FORMAT (JSON):
{{
  "intent": "chat|help_needed",
  "language_used": "target|native|other",
  "needs_clarification": true/false,
  "clarification_reason": "wrong_language|off_topic|unclear",
  "segments": [
    {{"type": "clarification", "text": "clarification question", "persona": "teacher"}},
    {{"type": "correction", "text": "corrected version", "persona": "teacher"}},
    {{"type": "help", "text": "explanation/translation", "persona": "teacher"}},
    {{"type": "response", "text": "conversation continuation", "persona": "partner"}}
  ]
}}

RULES:
- Include ONLY segments that are needed
- Teacher speaks in {native_lang}, Partner in {language}
- Keep responses concise and natural
- Always include a response segment to continue conversation
- If message is in wrong language, add clarification segment
- If message is off-topic/unclear, add clarification segment
"""
        
        return prompt
    
    def _format_conversation_context(self, recent_messages: List[Dict]) -> str:
        """Format recent messages for context"""
        if not recent_messages:
            return "No previous messages"
        
        formatted = []
        for msg in recent_messages[-6:]:  # Last 6 messages
            formatted.append(f"{msg['sender'].upper()}: {msg['content']}")
        
        return "\n".join(formatted)
    
    def _get_personalization_context(self, user_data: Dict) -> str:
        """Get personalization context (placeholder for Neo4j integration)"""
        personalization = user_data.get('personalization', {})
        if not personalization:
            return ""
        
        items = []
        if personalization.get('interests'):
            items.append(f"- Interests: {personalization['interests']}")
        if personalization.get('occupation'):
            items.append(f"- Occupation: {personalization['occupation']}")
        
        return "\n".join(items) if items else ""
    
    def _build_segments_from_result(self, result: Dict, user_data: Dict) -> List[Dict]:
        """Convert LLM result to segments"""
        segments = []
        
        # Process each segment from the result
        for i, segment in enumerate(result.get('segments', [])):
            segments.append({
                'type': segment['type'],
                'text': segment['text'],
                'persona': segment.get('persona', 'partner'),
                'timing': i * 800  # Simple timing
            })
        
        # Ensure we always have a response
        if not any(s['type'] == 'response' for s in segments):
            segments.append({
                'type': 'response',
                'text': self._get_fallback_text(user_data['learningLanguage']),
                'persona': 'partner',
                'timing': len(segments) * 800
            })
        
        return segments
    
    def _get_fallback_response(self, message: str, user_data: Dict) -> Dict:
        """Fallback if LLM fails to return valid JSON"""
        return {
            'intent': 'chat',
            'segments': [{
                'type': 'response',
                'text': self._get_fallback_text(user_data['learningLanguage']),
                'persona': 'partner'
            }]
        }
    
    def _get_fallback_text(self, language: str) -> str:
        """Get fallback text in target language"""
        fallbacks = {
            'Spanish': '¿Puedes repetir eso?',
            'French': 'Pouvez-vous répéter?',
            'German': 'Können Sie das wiederholen?',
            'English': 'Could you repeat that?'
        }
        return fallbacks.get(language, 'Could you repeat that?')
    
    def _get_error_response(self, user_data: Optional[Dict], error: str) -> Dict:
        """Generate error response"""
        language = user_data.get('learningLanguage', 'English') if user_data else 'English'
        error_message = get_error_message(language)
        
        return {
            'segments': [{
                'type': 'error',
                'text': error_message,
                'audio_data': None,
                'timing': 0
            }],
            'intent': 'error',
            'audio_language': language,
            'error': error
        }
    