from datetime import datetime
import uuid

class User:
    def __init__(self, username, email, password_hash, native_language, learning_language):
        self.id = str(uuid.uuid4())
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.native_language = native_language
        self.learning_language = learning_language
        self.created_at = datetime.utcnow().isoformat()
        self.personalization = {}
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'nativeLanguage': self.native_language,
            'learningLanguage': self.learning_language,
            'created_at': self.created_at,
            'personalization': self.personalization
        }
    
    def to_public_dict(self):
        """Return user data without sensitive information"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'nativeLanguage': self.native_language,
            'learningLanguage': self.learning_language,
            'created_at': self.created_at,
            'personalization': self.personalization
        }
    
    @classmethod
    def from_dict(cls, data):
        user = cls(
            username=data['username'],
            email=data['email'],
            password_hash=data['password_hash'],
            native_language=data['nativeLanguage'],
            learning_language=data['learningLanguage']
        )
        user.id = data['id']
        user.created_at = data['created_at']
        user.personalization = data.get('personalization', {})
        return user