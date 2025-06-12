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
        """Simple intent detection"""
        # Your existing logic
        pass
    
    def build_chat_prompt(self, user, conversation_context, current_message):
        """Build optimized prompt for chatbot"""
        # Your existing logic - returns the system prompt string
        pass
    
    def generate_response(self, user_id, message_content, audio_speed=0.8):
        """Main method to generate chat response"""
        try:
            user_data = find_user_by_id(user_id)
            if not user_data:
                raise ValueError("User not found")
            
            intent = self.detect_intent(
                message_content, 
                user_data['nativeLanguage'], 
                user_data['learningLanguage']
            )
            
            if intent == 'teaching':
                response_text = f"I detected you need help! For now, I'll continue chatting in {user_data['learningLanguage']}. Teaching mode coming soon!"
                audio_data = self.audio_service.generate_audio(response_text, user_data['learningLanguage'], audio_speed)
                
                return {
                    'response': response_text,
                    'intent': 'teaching',
                    'audio_language': user_data['learningLanguage'],
                    'audio_data': audio_data
                }
            
            # Add user message
            self.conversation_service.add_message(
                user_id, message_content, 'user', intent, user_data['learningLanguage']
            )
            
            # Get context and build prompt
            conversation_context = self.conversation_service.get_conversation_context(user_id)
            prompt = self.build_chat_prompt(user_data, conversation_context, message_content)
            
            # Generate LLM response
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": message_content}
            ]
            bot_response_content = self.llm_service.generate_chat_response(messages)
            
            # Generate audio
            audio_data = self.audio_service.generate_audio(
                bot_response_content, 
                user_data['learningLanguage'],
                audio_speed
            )
            
            # Save bot response
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
            # Error handling with audio service
            error_message = get_error_message(user_data.get('learningLanguage', 'English'))
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
        """Get conversation history"""
        return self.conversation_service.get_conversation_history(user_id)
    
    def start_new_session(self, user_id):
        """Start new conversation session"""
        self.audio_service.clear_cache()
        self.conversation_service.start_new_session(user_id)
        return {"message": "New session started"}