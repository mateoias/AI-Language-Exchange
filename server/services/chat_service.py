import openai
import azure.cognitiveservices.speech as speechsdk
from ..models.conversation import Conversation, Message
from ..utils.file_utils import find_user_by_id
from .conversation_service import ConversationService
from ..language_config import get_voice_name, get_pause_durations, get_error_message

from flask import current_app
import json
import os
import base64
import io

class ChatService:
    def __init__(self):
        self._openai_client = None
        self._speech_config = None
        self.conversation_service = ConversationService()
        # Cache for audio data during session
        self._audio_cache = {}
    
    @property
    def openai_client(self):
        """Lazy initialization of OpenAI client"""
        if self._openai_client is None:
            api_key = current_app.config.get('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            self._openai_client = openai.OpenAI(api_key=api_key)
        return self._openai_client
    
    @property
    def speech_config(self):
        """Lazy initialization of Azure Speech config"""
        if self._speech_config is None:
            speech_key = current_app.config.get('AZURE_SPEECH_KEY')
            speech_region = current_app.config.get('AZURE_SPEECH_REGION')
            if not speech_key or not speech_region:
                raise ValueError("Azure Speech credentials not configured")
            self._speech_config = speechsdk.SpeechConfig(
                subscription=speech_key, 
                region=speech_region
            )
            # Set to MP3 format for smaller size and faster transmission
            self._speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
            )
        return self._speech_config
    
    def _get_voice_name(self, language, voice_type='male'):
        """Map language to Azure voice name using language config"""
        return get_voice_name(language, voice_type)

    def _add_speech_marks(self, text, speed_rate=1.0, voice_name="en-US-AriaNeural"):
        """Add SSML markup for natural pauses, speed, and voice"""
        prosody_rate = f"{speed_rate:.1f}"
        
        # Get pause durations from config
        pauses = get_pause_durations()
        pause_multiplier = 1.0 / speed_rate
        
        # Calculate pause durations based on speed
        sentence_pause = int(pauses['sentence'] * pause_multiplier)
        comma_pause = int(pauses['comma'] * pause_multiplier)
        semicolon_pause = int(pauses['semicolon'] * pause_multiplier)
        
        # Apply pauses
        text = text.replace('.', f'.<break time="{sentence_pause}ms"/>')
        text = text.replace(',', f',<break time="{comma_pause}ms"/>')
        text = text.replace('!', f'!<break time="{sentence_pause}ms"/>')
        text = text.replace('?', f'?<break time="{sentence_pause}ms"/>')
        text = text.replace(';', f';<break time="{semicolon_pause}ms"/>')

        ssml = f'''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <voice name="{voice_name}">
                <prosody rate="{prosody_rate}">
                    {text}
                </prosody>
            </voice>
        </speak>'''
        
        return ssml
    
    def generate_audio(self, text, language, speed_rate=0.8):
        """Generate audio using Azure TTS"""
        try:
            # Check cache first
            cache_key = f"{text}_{language}_{speed_rate}"
            if cache_key in self._audio_cache:
                return self._audio_cache[cache_key]
            
            # Set voice based on language
            voice_name = self._get_voice_name(language)
            self.speech_config.speech_synthesis_voice_name = voice_name
            
            # Create synthesizer without audio config to get audio data directly
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=None  # This will return audio data in result
            )
            
            # Add SSML markup for pauses and speed
            ssml_text = self._add_speech_marks(text, speed_rate, voice_name)
            
            # Synthesize speech
            result = synthesizer.speak_ssml_async(ssml_text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # Get audio data directly from result
                audio_data = result.audio_data
                
                # Encode as base64
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                
                # Cache the result
                self._audio_cache[cache_key] = audio_base64
                print(f"Generated audio with speed: {speed_rate}")

                return audio_base64
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                print(f"Speech synthesis canceled: {cancellation.reason}")
                if cancellation.reason == speechsdk.CancellationReason.Error:
                    print(f"Error details: {cancellation.error_details}")
                return None
            else:
                print(f"Speech synthesis failed: {result.reason}")
                return None
                
        except Exception as e:
            print(f"Error generating audio: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
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
    
    def build_chat_prompt(self, user, conversation_context, current_message):
        """Build optimized prompt for chatbot with enhanced memory"""
        
        # Base system prompt
        system_prompt = f"""You are a friendly language exchange partner helping {user['username']} practice {user['learningLanguage']}. 

You are having a natural conversation to help them improve their language skills through practice.

User Details:
- Native Language: {user['nativeLanguage']}
- Learning: {user['learningLanguage']}
- Name: {user['username']}"""

        # Add personalization if available
        if user.get('personalization'):
            p = user['personalization']
            if p.get('currentLocation'):
                system_prompt += f"\n- Location: {p['currentLocation']}"
            if p.get('workStudy'):
                system_prompt += f"\n- Work/Study: {p['workStudy']}"

        system_prompt += f"""

Guidelines:
- Always respond in {user['learningLanguage']}
- Keep responses brief and conversational (2-3 sentences max)
- ALWAYS ask a follow-up question at the end of each response to continue the conversation
- Be encouraging and patient
- Correct major errors gently by using the correct form in your response
- Show genuine interest in the user's responses
- Vary your questions to keep the conversation engaging"""

        # Add conversation summaries for long-term memory
        if conversation_context['conversation_summaries']:
            system_prompt += "\n\nPrevious conversation highlights:"
            for summary in conversation_context['conversation_summaries']:
                system_prompt += f"\n{summary}"

        # Add recent conversation context
        if conversation_context['recent_messages']:
            system_prompt += "\n\nRecent conversation:"
            for msg in conversation_context['recent_messages']:
                system_prompt += f"\n{msg['sender']}: {msg['content']}"

        # Add behavior instructions
        system_prompt += f"\n\nRemember to always use {user['learningLanguage']} and keep your response brief. Ask a question at the end of each response."
        
        return system_prompt
    
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
                audio_data = self.generate_audio(response_text, user_data['learningLanguage'], audio_speed)
                
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
            
            # Build prompt with enhanced context
            prompt = self.build_chat_prompt(user_data, conversation_context, message_content)
            
            # Call OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": message_content}
                ],
                temperature=0.3,  # Low creativity for consistency
                max_tokens=150,   # Keep responses brief
            )
            
            bot_response_content = response.choices[0].message.content.strip()
            
            # Generate audio for the response
            audio_data = self.generate_audio(
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
                'audio_data': audio_data
            }
            
        except Exception as e:
            # Graceful error handling
            error_message = get_error_message(user_data.get('learningLanguage', 'English') if user_data else 'English')
            audio_data = None
            
            if user_data:
                try:
                    audio_data = self.generate_audio(
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
        """Start new conversation session and clear audio cache"""
        # Clear audio cache for this session
        self._audio_cache.clear()
        
        self.conversation_service.start_new_session(user_id)
        return {"message": "New session started"}