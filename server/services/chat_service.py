from .llm_service import LLMService
from .audio_service import AudioService
from .conversation_service import ConversationService
from ..utils.file_utils import find_user_by_id
from ..language_config import get_error_message

class ChatService:
    def __init__(self):
        self.llm_service = LLMService()
        self.audio_service = AudioService()
        self.conversation_service = ConversationService()
    
    def detect_intent(self, message, user_native_language, user_learning_language):
        """Simple intent detection based on language."""
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
    
    def regenerate_audio(self, text, language, speed_rate=0.8):
        """Regenerate audio for existing text"""
        return self.audio_service.generate_audio(text, language, speed_rate)
    
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
            
            # Build prompt with enhanced context
            prompt = self.build_chat_prompt(user_data, conversation_context, message_content)
            
            # Call OpenAI
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": message_content}
            ]
            bot_response_content = self.llm_service.generate_chat_response(messages)
            
            # Generate audio for the response
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
                'audio_data': audio_data
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
        """Start new conversation session and clear audio cache"""
        # Clear audio cache for this session
        self.audio_service.clear_cache()
        
        self.conversation_service.start_new_session(user_id)
        return {"message": "New session started"}