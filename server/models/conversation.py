from datetime import datetime
import uuid

class Message:
    def __init__(self, content, sender, intent=None, audio_language=None):
        self.id = str(uuid.uuid4())
        self.content = content
        self.sender = sender  # 'user' or 'bot'
        self.timestamp = datetime.utcnow().isoformat()
        self.intent = intent  # 'chat' or 'teaching'
        self.audio_language = audio_language
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'sender': self.sender,
            'timestamp': self.timestamp,
            'intent': self.intent,
            'audio_language': self.audio_language
        }
    
    @classmethod
    def from_dict(cls, data):
        message = cls(
            content=data['content'],
            sender=data['sender'],
            intent=data.get('intent'),
            audio_language=data.get('audio_language')
        )
        message.id = data['id']
        message.timestamp = data['timestamp']
        return message

class Conversation:
    def __init__(self, user_id):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.created_at = datetime.utcnow().isoformat()
        self.messages = []
        self.summary = ""
        self.current_topic = ""
    
    def add_message(self, message):
        self.messages.append(message)
    
    def get_recent_messages(self, limit=6):
        """Get the most recent messages for context"""
        return self.messages[-limit:] if len(self.messages) > limit else self.messages
    
    def get_message_count(self):
        return len(self.messages)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'created_at': self.created_at,
            'messages': [msg.to_dict() for msg in self.messages],
            'summary': self.summary,
            'current_topic': self.current_topic
        }
    
    @classmethod
    def from_dict(cls, data):
        conversation = cls(data['user_id'])
        conversation.id = data['id']
        conversation.created_at = data['created_at']
        conversation.summary = data.get('summary', '')
        conversation.current_topic = data.get('current_topic', '')
        conversation.messages = [Message.from_dict(msg_data) for msg_data in data['messages']]
        return conversation