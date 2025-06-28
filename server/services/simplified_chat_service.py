# server/services/simplified_chat_service.py - OPTIMIZED VERSION
"""
OPTIMIZED simplified chat service with concise prompts and performance focus
"""
import json
from typing import Dict, List, Optional
from .llm_manager import llm_manager
from .prompt_builder import PromptBuilder
from .audio_queue_service import AudioQueueService
from .conversation_service import ConversationService
from ..utils.file_utils import find_user_by_id
from ..language_config import get_error_message
from datetime import datetime

class SimplifiedChatService:
    """
    OPTIMIZED simplified chat service - focused on speed and simplicity
    """
    
    def __init__(self, speech_key=None, speech_region=None):
        self.conversation_service = ConversationService()
        self.prompt_builder = PromptBuilder()
        self.speech_key = speech_key
        self.speech_region = speech_region
        
        # Only initialize audio services if credentials provided
        if speech_key and speech_region:
            self.audio_queue_service = AudioQueueService(speech_key, speech_region)
        else:
            self.audio_queue_service = None
    
    def generate_response(self, user_id, message_content, audio_speed=0.8, skip_audio=False):
        """
        Generate complete response with single LLM call - OPTIMIZED VERSION
        """
        print(f"\n🚀 OPTIMIZED SIMPLIFIED SERVICE - Starting")
        print(f"   Message: '{message_content}' | Audio: {'disabled' if skip_audio else 'enabled'}")
        
        try:
            # Get user data
            user_data = find_user_by_id(user_id)
            if not user_data:
                raise ValueError("User not found")
            
            # Get conversation context
            conversation_context = self.conversation_service.get_conversation_context(user_id)
            
            # Add user message to conversation
            self.conversation_service.add_message(
                user_id, message_content, 'user', 'chat', user_data['learningLanguage']
            )
            
            level = user_data.get('proficiencyLevel', 'beginner')
            print(f"   Level: {level} | Learning: {user_data['learningLanguage']}")
            
            # Build CONCISE prompt
            system_prompt = self._build_concise_prompt(user_data, conversation_context, message_content)
            
            print(f"   Prompt length: {len(system_prompt)} chars")
            
            # Single LLM call with reduced token limit
            print(f"🤖 Making optimized LLM call...")
            start_time = datetime.now()
            
            response_text = llm_manager.generate_chat_response(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message_content}
                ],
                temperature=0.7,
                max_tokens=200,  # REDUCED from 400
                log_request=True
            )
            
            llm_duration = (datetime.now() - start_time).total_seconds() * 1000
            print(f"   ✅ LLM completed in {llm_duration:.0f}ms")
            
            # Parse response
            segments = self._parse_optimized_response(response_text, user_data, level)
            print(f"   📊 Generated {len(segments)} segments")
            
            # Audio generation (optional)
            if not skip_audio and self.audio_queue_service and segments:
                print(f"🎵 Generating audio...")
                audio_start = datetime.now()
                
                segments_with_audio = self.audio_queue_service.generate_audio_segments(
                    segments,
                    user_data['learningLanguage'],
                    audio_speed,
                    user_data['nativeLanguage']
                )
                
                audio_duration = (datetime.now() - audio_start).total_seconds() * 1000
                print(f"   🎵 Audio completed in {audio_duration:.0f}ms")
            else:
                segments_with_audio = segments
                audio_duration = 0
            
            # Add bot response to conversation
            main_response = next(
                (s['text'] for s in segments if s['type'] == 'response'), 
                "I'm here to help!"
            )
            self.conversation_service.add_message(
                user_id, main_response, 'bot', 'chat', user_data['learningLanguage']
            )
            
            total_duration = (datetime.now() - start_time).total_seconds() * 1000
            print(f"✅ TOTAL TIME: {total_duration:.0f}ms (LLM: {llm_duration:.0f}ms, Audio: {audio_duration:.0f}ms)")
            
            return {
                'segments': segments_with_audio,
                'intent': 'chat',
                'audio_language': user_data['learningLanguage'],
                'performance': {
                    'llm_time_ms': llm_duration,
                    'audio_time_ms': audio_duration,
                    'total_time_ms': total_duration,
                    'approach': 'optimized_simplified',
                    'prompt_length': len(system_prompt),
                    'audio_enabled': not skip_audio
                }
            }
            
        except Exception as e:
            print(f"❌ Error in optimized service: {e}")
            import traceback
            traceback.print_exc()
            return self._error_response(user_data, str(e))
    
    def _build_concise_prompt(self, user_data: Dict, conversation_context: Dict, message: str) -> str:
        """
        Build a MUCH more concise prompt focused on speed
        """
        level = user_data.get('proficiencyLevel', 'beginner')
        learning_lang = user_data['learningLanguage']
        native_lang = user_data['nativeLanguage']
        
        # Get recent conversation for context
        recent_messages = conversation_context.get('recent_messages', [])[-3:]  # Only last 3
        
        # Build minimal conversation context
        if recent_messages:
            context_str = "Recent conversation:\n" + "\n".join([
                f"{msg['sender']}: {msg['content']}" for msg in recent_messages[-2:]
            ])
        else:
            context_str = "This is the start of your conversation."
        
        # Level-specific rules (MUCH shorter)
        if level == 'beginner':
            rephrase_rule = "Rephrase short answers (1-3 words) into complete sentences."
            response_rule = "Use simple words, short sentences. Always ask yes/no questions."
        elif level == 'intermediate':
            rephrase_rule = "Only rephrase very short answers (1-2 words) or obvious errors."
            response_rule = "Use varied vocabulary, ask open questions."
        else:  # advanced
            rephrase_rule = "Rarely rephrase - only for major errors."
            response_rule = "Natural conversation, discuss complex topics."
        
        # CONCISE prompt
        prompt = f"""You help {user_data.get('username', 'the student')} practice {learning_lang}.

{context_str}

LEVEL: {level}
RULES: {rephrase_rule} {response_rule}

RESPOND WITH JSON:
{{
  "rephrase": "complete sentence version (only if needed)",
  "response": "your reply in {learning_lang}",
  "include_rephrase": true/false
}}

Student said: "{message}"
Be concise and natural."""

        return prompt
    
    def _parse_optimized_response(self, response_text: str, user_data: Dict, level: str) -> List[Dict]:
        """Parse the optimized JSON response"""
        try:
            data = json.loads(response_text)
            segments = []
            
            # Add rephrase if included
            if data.get('include_rephrase', False) and data.get('rephrase'):
                segments.append({
                    'type': 'rephrase',
                    'text': data['rephrase'],
                    'persona': 'teacher',
                    'timing': 0
                })
            
            # Add response
            if data.get('response'):
                segments.append({
                    'type': 'response',
                    'text': data['response'],
                    'persona': 'partner',
                    'timing': len(segments) * 800
                })
            
            return segments
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️  JSON parsing failed: {e}")
            print(f"   Raw response: {response_text[:200]}...")
            
            # Fallback: treat as conversation response
            return [{
                'type': 'response',
                'text': response_text.strip(),
                'persona': 'partner',
                'timing': 0
            }]
    
    def _error_response(self, user_data: Dict, error_msg: str) -> Dict:
        """Generate error response"""
        error_message = get_error_message(
            user_data.get('learningLanguage', 'English') if user_data else 'English'
        )
        
        return {
            'segments': [{
                'type': 'error',
                'text': error_message,
                'audio_data': None,
                'timing': 0,
                'persona': 'partner'
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
        return self.conversation_service.start_new_session(user_id)