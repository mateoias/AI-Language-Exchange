import json
import os
from threading import Lock
from flask import current_app
from datetime import datetime
import uuid

# File lock for conversation operations
conversation_lock = Lock()

def get_user_conversations_file(user_id):
    """Get the conversation file path for a user"""
    conversations_dir = os.path.join(current_app.config['DATA_DIR'], 'conversations')
    os.makedirs(conversations_dir, exist_ok=True)
    return os.path.join(conversations_dir, f'{user_id}.json')

def load_user_conversations(user_id):
    """Load all conversations for a user"""
    conversations_file = get_user_conversations_file(user_id)
    
    if not os.path.exists(conversations_file):
        return {
            'user_id': user_id,
            'conversations': [],
            'current_conversation_id': None
        }
    
    try:
        with open(conversations_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {
            'user_id': user_id,
            'conversations': [],
            'current_conversation_id': None
        }

def save_user_conversations(user_id, conversations_data):
    """Save conversations to file with thread safety"""
    conversations_file = get_user_conversations_file(user_id)
    
    with conversation_lock:
        try:
            with open(conversations_file, 'w', encoding='utf-8') as f:
                json.dump(conversations_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving conversations for user {user_id}: {e}")
            return False

def create_new_conversation(user_id):
    """Create a new conversation for a user"""
    return {
        'id': str(uuid.uuid4()),
        'user_id': user_id,
        'created_at': datetime.utcnow().isoformat(),
        'messages': [],
        'summary': ''
    }

def add_message_to_conversation(conversations_data, message_data):
    """Add a message to the current conversation"""
    current_conv_id = conversations_data['current_conversation_id']
    
    if not current_conv_id:
        # Create new conversation
        new_conv = create_new_conversation(conversations_data['user_id'])
        conversations_data['conversations'].append(new_conv)
        conversations_data['current_conversation_id'] = new_conv['id']
        current_conv_id = new_conv['id']
    
    # Find current conversation
    current_conv = None
    for conv in conversations_data['conversations']:
        if conv['id'] == current_conv_id:
            current_conv = conv
            break
    
    if current_conv:
        current_conv['messages'].append(message_data)
    
    return conversations_data

def get_current_conversation(conversations_data):
    """Get the current active conversation"""
    current_conv_id = conversations_data['current_conversation_id']
    
    if not current_conv_id:
        return None
    
    for conv in conversations_data['conversations']:
        if conv['id'] == current_conv_id:
            return conv
    
    return None

def get_recent_messages(conversations_data, limit=10):
    """Get recent messages from current conversation"""
    current_conv = get_current_conversation(conversations_data)
    
    if not current_conv:
        return []
    
    messages = current_conv['messages']
    return messages[-limit:] if len(messages) > limit else messages

def should_summarize_conversation(conversations_data):
    """Check if current conversation needs summarization"""
    current_conv = get_current_conversation(conversations_data)
    
    if not current_conv:
        return False
    
    # Summarize every 10 messages (only count user messages)
    user_messages = [msg for msg in current_conv['messages'] if msg['sender'] == 'user']
    return len(user_messages) > 0 and len(user_messages) % 5 == 0  # Every 5 user messages (10 total)

def cleanup_old_conversations(conversations_data, keep_count=5):
    """Keep only the most recent conversations"""
    conversations = conversations_data['conversations']
    
    if len(conversations) > keep_count:
        # Sort by created_at and keep most recent
        conversations.sort(key=lambda x: x['created_at'], reverse=True)
        conversations_data['conversations'] = conversations[:keep_count]
        
        # Make sure current conversation is still valid
        current_id = conversations_data['current_conversation_id']
        valid_ids = [conv['id'] for conv in conversations_data['conversations']]
        
        if current_id not in valid_ids:
            conversations_data['current_conversation_id'] = conversations[0]['id'] if conversations else None
    
    return conversations_data

def start_new_conversation(user_id):
    """Start a new conversation session"""
    conversations_data = load_user_conversations(user_id)
    
    # Create new conversation
    new_conv = create_new_conversation(user_id)
    conversations_data['conversations'].append(new_conv)
    conversations_data['current_conversation_id'] = new_conv['id']
    
    # Cleanup old conversations
    conversations_data = cleanup_old_conversations(conversations_data)
    
    # Save to file
    save_user_conversations(user_id, conversations_data)
    
    return conversations_data