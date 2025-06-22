# services/conversation_service.py
from .llm_manager import llm_manager
from datetime import datetime
from ..utils.conversation_utils import (
    load_user_conversations, save_user_conversations, add_message_to_conversation,
    get_recent_messages, should_summarize_conversation, get_current_conversation,
    start_new_conversation
)

class ConversationService:
    def __init__(self):
        pass  # No more OpenAI client needed
    
    def generate_conversation_summary(self, messages):
        """Generate a summary of conversation messages using GPT-4"""
        try:
            # Prepare messages for summarization
            conversation_text = "\n".join([
                f"{msg['sender']}: {msg['content']}" for msg in messages
            ])
            
            # Use centralized LLM manager for summary generation
            summary = llm_manager.generate_summary(conversation_text)
            return summary
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Summary unavailable"
    def generate_chunk_summary(self, messages, chunk_number):
        """Generate a summary focused on conversation flow for continuing the chat"""
        try:
            # Prepare messages for conversation flow summary
            conversation_text = "\n".join([
                f"{msg['sender']}: {msg['content']}" for msg in messages
            ])
            
            summary_prompt = f"""Create a brief summary of this conversation chunk (messages {chunk_number*10-9} to {chunk_number*10}) 
    focusing on the conversation flow and context needed to continue naturally. Include:
    - What topics were being discussed
    - The direction the conversation was heading
    - Any questions asked but not fully answered
    - The mood/tone of the conversation

    Keep it under 100 words and write it as context for continuing this conversation.

    Conversation:
    {conversation_text}"""

            summary = llm_manager.generate_chat_response(
                messages=[
                    {"role": "system", "content": "You are creating conversation flow summaries."},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )
            return summary
            
        except Exception as e:
            print(f"Error generating chunk summary: {e}")
            return "Summary unavailable"

    def generate_conversation_analysis(self, messages, user_data):
        """Generate comprehensive analysis for database storage"""
        try:
            conversation_text = "\n".join([
                f"{msg['sender']}: {msg['content']}" for msg in messages
            ])
            
            analysis_prompt = f"""Analyze this {user_data['learningLanguage']} language learning conversation. 
    Extract and structure the following information:

    1. Topics discussed (list all topics)
    2. Vocabulary used (list new/challenging words the user encountered)
    3. Grammar patterns practiced
    4. Errors made and corrections provided
    5. User's strengths demonstrated
    6. Areas needing improvement
    7. Conversation engagement level (1-10)
    8. Recommended focus areas for next session

    Conversation:
    {conversation_text}

    Provide the analysis in a structured format."""

            analysis = llm_manager.generate_chat_response(
                messages=[
                    {"role": "system", "content": "You are a language learning analyst."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return {
                'analysis': analysis,
                'message_count': len(messages),
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': user_data.get('id'),
                'learning_language': user_data.get('learningLanguage')
            }
            
        except Exception as e:
            print(f"Error generating conversation analysis: {e}")
            return None

    def add_message(self, user_id, message_content, sender, intent=None, audio_language=None):
        """Add a message to user's conversation and handle summarization"""
        # Load user conversations
        conversations_data = load_user_conversations(user_id)
        
        # Create message data
        message_data = {
            'content': message_content,
            'sender': sender,
            'timestamp': datetime.utcnow().isoformat(),
            'intent': intent,
            'audio_language': audio_language
        }
        
        # Add message to conversation
        conversations_data = add_message_to_conversation(conversations_data, message_data)
        
        # Get current conversation
        current_conv = get_current_conversation(conversations_data)
        if current_conv:
            message_count = len(current_conv['messages'])
            
            # Initialize chunk_summaries if not present
            if 'chunk_summaries' not in current_conv:
                current_conv['chunk_summaries'] = []
            
            # Check if we need a chunk summary (every 10 messages, after bot response)
            if message_count % 10 == 0 and sender == 'bot':
                chunk_number = message_count // 10
                start_idx = (chunk_number - 1) * 10
                end_idx = chunk_number * 10
                
                chunk_messages = current_conv['messages'][start_idx:end_idx]
                print(f"Generating chunk summary for messages {start_idx+1}-{end_idx}")
                
                chunk_summary = self.generate_chunk_summary(chunk_messages, chunk_number)
                current_conv['chunk_summaries'].append({
                    'chunk_number': chunk_number,
                    'summary': chunk_summary,
                    'message_range': f"{start_idx+1}-{end_idx}",
                    'created_at': datetime.utcnow().isoformat()
                })
        
    # Save conversations
        save_user_conversations(user_id, conversations_data)
    
        return conversations_data
    
    def get_conversation_context(self, user_id):
        """Get conversation context for prompt building"""
        conversations_data = load_user_conversations(user_id)
        
        # Get recent messages from current conversation (up to 10)
        recent_messages = get_recent_messages(conversations_data, limit=10)
        
        # Get chunk summaries from current conversation
        current_conv = get_current_conversation(conversations_data)
        chunk_summaries = []
        
        if current_conv and 'chunk_summaries' in current_conv:
            # Get the most recent 2 chunk summaries for context
            chunk_summaries = current_conv['chunk_summaries'][-2:]
        
        # Get summaries from previous conversations
        conversation_summaries = []
        current_conv_id = conversations_data.get('current_conversation_id')
        
        for conv in conversations_data.get('conversations', []):
            if conv['id'] != current_conv_id and conv.get('summary'):
                conversation_summaries.append(conv['summary'])
        
        return {
            'recent_messages': recent_messages,
            'chunk_summaries': chunk_summaries,  # New field
            'conversation_summaries': conversation_summaries[-3:],
            'message_count': len(recent_messages),
            'total_messages_in_conversation': len(current_conv['messages']) if current_conv else 0
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
    
    def finalize_conversation(self, user_id):
        """Finalize current conversation for database storage"""
        from ..utils.file_utils import find_user_by_id
        
        conversations_data = load_user_conversations(user_id)
        current_conv = get_current_conversation(conversations_data)
        
        if not current_conv or len(current_conv['messages']) == 0:
            return None
        
        # Get user data for analysis
        user_data = find_user_by_id(user_id)
        
        # Generate final comprehensive summary if not exists
        if not current_conv.get('summary'):
            print(f"Generating final summary for conversation {current_conv['id']}")
            current_conv['summary'] = self.generate_conversation_summary(current_conv['messages'])
        
        # Generate detailed analysis for database
        analysis = self.generate_conversation_analysis(current_conv['messages'], user_data)
        
        # Prepare data for database
        db_ready_data = {
            'conversation_id': current_conv['id'],
            'user_id': user_id,
            'created_at': current_conv['created_at'],
            'message_count': len(current_conv['messages']),
            'messages': current_conv['messages'],
            'chunk_summaries': current_conv.get('chunk_summaries', []),
            'final_summary': current_conv['summary'],
            'analysis': analysis,
            'finalized_at': datetime.utcnow().isoformat()
        }
        
        # Send to Neo4j database
        # neo4j_service.store_conversation(db_ready_data)
        
        return db_ready_data