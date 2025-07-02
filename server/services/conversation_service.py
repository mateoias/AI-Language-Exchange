# services/conversation_service.py
import uuid
from .llm_manager import llm_manager
from datetime import datetime
from ..utils.conversation_utils import (
    load_user_conversations, save_user_conversations, add_message_to_conversation,
    get_recent_messages, should_summarize_conversation, get_current_conversation,
    start_new_conversation, clear_conversation_memory  # Add this import
)

import logging
logger = logging.getLogger(__name__)

class ConversationService:
    def __init__(self):
        pass 
    
    def generate_conversation_summary(self, messages):
        """Generate a summary of conversation messages using GPT-4"""
        try:
            if not messages or len(messages) == 0:
                return "Empty conversation - no messages to summarize"
            
            conversation_text = "\n".join([
                f"{msg['sender']}: {msg['content']}" for msg in messages
            ])
            
            summary = llm_manager.generate_summary(conversation_text)
            return summary
        
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Summary unavailable"
        
    def generate_chunk_summary(self, messages, chunk_number):
        """Generate a summary focused on conversation flow for continuing the chat"""
        try:
            if not messages or len(messages) == 0:
                return "Empty chunk"
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
            # Initialize chunk_summaries if not present
            if 'chunk_summaries' not in current_conv:
                current_conv['chunk_summaries'] = []
            
            # Count message pairs (user + bot = 1 exchange)
            user_messages = [msg for msg in current_conv['messages'] if msg['sender'] == 'user']
            bot_messages = [msg for msg in current_conv['messages'] if msg['sender'] == 'bot']
            
            # Generate chunk summary every 5 exchanges (10 messages)
            # Only after bot responds to maintain conversation flow
            if sender == 'bot' and len(user_messages) > 0 and len(user_messages) % 5 == 0:
                # Calculate which messages to summarize
                chunk_number = len(user_messages) // 5
                start_idx = (chunk_number - 1) * 10
                end_idx = min(chunk_number * 10, len(current_conv['messages']))
                
                chunk_messages = current_conv['messages'][start_idx:end_idx]
                
                print(f"[CHUNK SUMMARY] Generating chunk {chunk_number} for messages {start_idx+1}-{end_idx}")
                print(f"[CHUNK SUMMARY] User messages: {len(user_messages)}, Bot messages: {len(bot_messages)}")
                
                chunk_summary = self.generate_chunk_summary(chunk_messages, chunk_number)
                current_conv['chunk_summaries'].append({
                    'chunk_number': chunk_number,
                    'summary': chunk_summary,
                    'message_range': f"{start_idx+1}-{end_idx}",
                    'created_at': datetime.utcnow().isoformat()
                })
                
                print(f"[CHUNK SUMMARY] Generated: {chunk_summary[:100]}...")
        
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
            print(f"[FINALIZE] No active conversation to finalize for user {user_id}")
            return None
        
        print(f"[FINALIZE] Finalizing conversation {current_conv['id']} with {len(current_conv['messages'])} messages")
        
        # Get user data for analysis
        user_data = find_user_by_id(user_id)
        
        # Always generate final comprehensive summary
        print(f"[FINALIZE] Generating final summary...")
        current_conv['summary'] = self.generate_conversation_summary(current_conv['messages'])
        print(f"[FINALIZE] Summary generated: {current_conv['summary'][:100]}...")
        
        # Generate detailed analysis for database
        print(f"[FINALIZE] Generating conversation analysis...")
        analysis = self.generate_conversation_analysis(current_conv['messages'], user_data)
        
        # Mark conversation as finalized
        current_conv['finalized'] = True
        current_conv['finalized_at'] = datetime.utcnow().isoformat()
        
        # Save the updated conversation
        save_user_conversations(user_id, conversations_data)
        
        # Prepare data for database (when ready)
        db_ready_data = {
            'conversation_id': current_conv['id'],
            'user_id': user_id,
            'created_at': current_conv['created_at'],
            'message_count': len(current_conv['messages']),
            'messages': current_conv['messages'],
            'chunk_summaries': current_conv.get('chunk_summaries', []),
            'final_summary': current_conv['summary'],
            'analysis': analysis,
            'finalized_at': current_conv['finalized_at']
        }
        
        print(f"[FINALIZE] Conversation finalized successfully")
        
        # need to Send to Neo4j database when implemented
        # neo4j_service.store_conversation(db_ready_data)
        
        return db_ready_data
    
    def start_new_session(self, user_id, save_current=False):
        """Start a new conversation session"""
        if save_current:
            # Save current conversation before starting new
            self.finalize_conversation(user_id)
        
        # Clear memory and start fresh
        return start_new_conversation(user_id, save_to_file=True)

    def clear_session_without_save(self, user_id):
        """Clear current session without saving (for UI refresh)"""
        # Import here to avoid circular import
        from ..utils.conversation_utils import save_user_conversations
        
        # Create a fresh conversation state
        cleared_data = {
            'user_id': user_id,
            'conversations': [],
            'current_conversation_id': None
        }
        
        # Create a new empty conversation
        new_conv = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat(),
            'messages': [],
            'summary': '',
            'chunk_summaries': []
        }
        
        cleared_data['conversations'] = [new_conv]
        cleared_data['current_conversation_id'] = new_conv['id']
        
        # Save the empty state
        save_user_conversations(user_id, cleared_data)
        return cleared_data