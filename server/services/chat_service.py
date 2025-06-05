import openai
from models.conversation import Conversation, Message
from utils.file_utils import find_user_by_id
from services.conversation_service import ConversationService
from flask import current_app
import json
import os

class ChatService:
    def __init__(self):
        self._openai_client = None
        self.conversation_service = ConversationService()  # NEW: Use conversation service
    
    @property
    def openai_client(self):
        """Lazy initialization of OpenAI client"""
        if self._openai_client is None:
            api_key = current_app.config.get('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            self._openai_client = openai.OpenAI(api_key=api_key)
        return self._openai_client
    
    def detect_intent(self, message, user_native_language, user_learning_language):
        """
        Simple intent detection based on language.
        Target language = chat mode
        Native language = teaching mode
        """
        # For MVP: Basic heuristic
        # TODO: Implement proper language detection
        
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
    
    def generate_response(self, user_id, message_content):
        """Main method to generate chat response with persistent memory"""
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
                return {
                    'response': f"I detected you need help! For now, I'll continue chatting in {user_data['learningLanguage']}. Teaching mode coming soon!",
                    'intent': 'teaching',
                    'audio_language': user_data['learningLanguage']
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
            
            # Add bot response to persistent conversation
            self.conversation_service.add_message(
                user_id, bot_response_content, 'bot', 'chat', user_data['learningLanguage']
            )
            
            return {
                'response': bot_response_content,
                'intent': 'chat',
                'audio_language': user_data['learningLanguage']
            }
            
        except Exception as e:
            # Graceful error handling
            return {
                'response': "I'm sorry, I'm having trouble right now. Please try again in a moment.",
                'intent': 'error',
                'audio_language': user_data.get('learningLanguage', 'English'),
                'error': str(e)
            }
    
    def get_conversation_history(self, user_id):
        """Get conversation history using persistent storage"""
        return self.conversation_service.get_conversation_history(user_id)
    
    def start_new_session(self, user_id):
        """Start new conversation session"""
        self.conversation_service.start_new_session(user_id)
        return {"message": "New session started"}