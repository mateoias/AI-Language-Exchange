import openai
from models.conversation import Conversation, Message
from utils.file_utils import find_user_by_id
from flask import current_app
import json
import os

class ChatService:
    def __init__(self):
        self._openai_client = None
        self.conversations = {}  # In-memory storage for current session
    
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
    
    def get_or_create_conversation(self, user_id):
        """Get existing conversation or create new one for this session"""
        if user_id not in self.conversations:
            self.conversations[user_id] = Conversation(user_id)
        return self.conversations[user_id]
    
    def build_chat_prompt(self, user, conversation, current_message):
        """Build optimized prompt for chatbot"""
        
        # Base system prompt
        system_prompt = f"""You are a friendly language exchange partner helping {user['username']} practice {user['learningLanguage']}. 
        
You are having a natural conversation to help them improve their language skills through practice.

User Details:
- Native Language: {user['nativeLanguage']}
- Learning: {user['learningLanguage']}
- Name: {user['username']}

Guidelines:
- Always respond in {user['learningLanguage']}
- Keep responses brief and conversational
- Ask a question at the end of each response to continue the conversation
- Be encouraging and patient
- Correct major errors gently by using the correct form in your response
"""
        
        # Add conversation context
        recent_messages = conversation.get_recent_messages(6)
        context = "\n".join([
            f"{msg.sender}: {msg.content}" for msg in recent_messages
        ])
        
        if context:
            system_prompt += f"\n\nRecent conversation:\n{context}"
        
        # Add current topic if available
        if conversation.current_topic:
            system_prompt += f"\n\nCurrent topic: {conversation.current_topic}"
        
        # Add behavior instructions
        system_prompt += f"\n\nRemember to always use {user['learningLanguage']} and keep your response brief. Ask a question at the end of each response."
        
        return system_prompt
    
    def generate_response(self, user_id, message_content):
        """Main method to generate chat response"""
        try:
            # Get user data
            user_data = find_user_by_id(user_id)
            if not user_data:
                raise ValueError("User not found")
            
            # Get or create conversation
            conversation = self.get_or_create_conversation(user_id)
            
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
            
            # Create user message
            user_message = Message(
                content=message_content,
                sender='user',
                intent=intent,
                audio_language=user_data['learningLanguage']
            )
            conversation.add_message(user_message)
            
            # Build prompt
            prompt = self.build_chat_prompt(user_data, conversation, message_content)
            
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
            
            # Create bot message
            bot_message = Message(
                content=bot_response_content,
                sender='bot',
                intent='chat',
                audio_language=user_data['learningLanguage']
            )
            conversation.add_message(bot_message)
            
            return {
                'response': bot_response_content,
                'intent': 'chat',
                'audio_language': user_data['learningLanguage'],
                'conversation_id': conversation.id
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
        """Get conversation history for current session"""
        if user_id in self.conversations:
            conversation = self.conversations[user_id]
            return {
                'conversation_id': conversation.id,
                'messages': [msg.to_dict() for msg in conversation.messages],
                'message_count': conversation.get_message_count()
            }
        return {'messages': [], 'message_count': 0}