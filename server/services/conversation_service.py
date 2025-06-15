import openai
from flask import current_app
from datetime import datetime
from ..utils.conversation_utils import (
    load_user_conversations, save_user_conversations, add_message_to_conversation,
    get_recent_messages, should_summarize_conversation, get_current_conversation,
    start_new_conversation
)

class ConversationService:
    def __init__(self):
        self._openai_client = None
    
    @property
    def openai_client(self):
        """Lazy initialization of OpenAI client"""
        if self._openai_client is None:
            api_key = current_app.config.get('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            self._openai_client = openai.OpenAI(api_key=api_key)
        return self._openai_client
    
    def generate_conversation_summary(self, messages):
        """Generate a summary of conversation messages using GPT-4"""
        try:
            # Prepare messages for summarization
            conversation_text = "\n".join([
                f"{msg['sender']}: {msg['content']}" for msg in messages
            ])
            
            summary_prompt = f"""Please create a concise bullet-point summary of this conversation between a language learner and AI tutor. Focus on:
- Key personal information shared by the user
- Topics discussed
- Language learning progress or challenges
- Important facts to remember for future conversations

Conversation:
{conversation_text}

Provide the summary as bullet points:"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise conversation summaries."},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Summary unavailable"
    
    def add_message(self, user_id, message_content, sender, intent=None, audio_language=None):
        """Add a message to user's conversation and handle summarization"""
        # Load user conversations
        conversations_data = load_user_conversations(user_id)
        
        # Create message data (ID will be generated in add_message_to_conversation)
        message_data = {
            'content': message_content,
            'sender': sender,
            'timestamp': datetime.utcnow().isoformat(),
            'intent': intent,
            'audio_language': audio_language
        }
        
        # Add message to conversation (this will generate the proper ID)
        conversations_data = add_message_to_conversation(conversations_data, message_data)
        
        # Check if we need to summarize
        if should_summarize_conversation(conversations_data) and sender == 'bot':  # Summarize after bot responses
            current_conv = get_current_conversation(conversations_data)
            if current_conv and not current_conv.get('summary'):
                print(f"Generating summary for conversation {current_conv['id']}")
                summary = self.generate_conversation_summary(current_conv['messages'])
                current_conv['summary'] = summary
        
        # Save conversations
        save_user_conversations(user_id, conversations_data)
        
        return conversations_data
    
    def get_conversation_context(self, user_id):
        """Get conversation context for prompt building"""
        conversations_data = load_user_conversations(user_id)
        
        # Get recent messages from current conversation
        recent_messages = get_recent_messages(conversations_data, limit=10)
        
        # Get summaries from previous conversations (excluding current)
        summaries = []
        current_conv_id = conversations_data.get('current_conversation_id')
        
        for conv in conversations_data.get('conversations', []):
            if conv['id'] != current_conv_id and conv.get('summary'):
                summaries.append(conv['summary'])
        
        return {
            'recent_messages': recent_messages,
            'conversation_summaries': summaries[-3:],  # Last 3 conversation summaries
            'message_count': len(recent_messages)
        }
    
    def start_new_session(self, user_id):
        """Start a new conversation session"""
        return start_new_conversation(user_id)
    
    def get_conversation_history(self, user_id):
        """Get conversation history for display"""
        conversations_data = load_user_conversations(user_id)
        recent_messages = get_recent_messages(conversations_data, limit=50)  # More for display
        
        return {
            'messages': recent_messages,
            'message_count': len(recent_messages)
        }