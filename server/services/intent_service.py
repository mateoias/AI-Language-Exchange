# server/services/intent_service.py
"""
Fast intent detection service for identifying user needs
"""
import re
from typing import Dict, Tuple

class IntentService:
    """
    Detects user intent quickly without using LLM for common patterns
    Falls back to LLM for complex cases
    """
    
    # Help patterns in various languages
    HELP_PATTERNS = {
        'english': [
            r'\bwhat does\b.*\bmean\b',
            r'\bwhat is\b',
            r"\bdon't understand\b",
            r'\bhelp\b',
            r'\bexplain\b',
            r'\bhow do you say\b',
            r'\bhow to say\b',
            r'\btranslate\b'
        ],
        'spanish': [
            r'\b(?:qué|que) (?:es|significa)\b',
            r'\bno (?:entiendo|comprendo)\b',
            r'\bayuda\b',
            r'\bexplica\b',
            r'\b(?:cómo|como) se dice\b',
            r'\btraducir\b',
            r'\bque quiere decir\b'
        ],
        'french': [
            r"\bqu'est-ce que\b",
            r'\bje ne comprends pas\b',
            r'\baide\b',
            r'\bexpliquer\b',
            r'\bcomment dit-on\b',
            r'\bque veut dire\b'
        ],
        'german': [
            r'\bwas (?:ist|bedeutet)\b',
            r'\bich verstehe nicht\b',
            r'\bhilfe\b',
            r'\berklär\b',
            r'\bwie sagt man\b',
            r'\bwas heißt\b'
        ]
    }
    
    # Short response patterns
    SHORT_RESPONSES = {
        'affirmative': [r'\b(?:yes|yeah|yep|sure|okay|ok|sí|si|oui|ja|da)\b'],
        'negative': [r'\b(?:no|nope|nicht|nein|non|niet)\b'],
        'uncertain': [r"\b(?:don't know|dunno|no sé|no se|sais pas|weiß nicht|nicht sicher)\b"]
    }
    
    def detect_intent(self, message: str, user_language: str) -> Dict[str, any]:
        """
        Quickly detect user intent from message
        
        Returns:
            {
                'intent': 'help_needed' | 'normal_chat' | 'correction_needed',
                'confidence': float (0-1),
                'details': {
                    'is_short': bool,
                    'needs_rephrase': bool,
                    'help_type': 'translation' | 'explanation' | None,
                    'response_type': 'affirmative' | 'negative' | 'uncertain' | None
                }
            }
        """
        message_lower = message.lower().strip()
        
        # Check if it's a short response
        is_short = len(message_lower.split()) <= 3
        
        # Check for help patterns
        help_needed, help_type = self._check_help_patterns(message_lower, user_language)
        
        # Check response type for short messages
        response_type = self._check_response_type(message_lower) if is_short else None
        
        # Determine intent
        if help_needed:
            intent = 'help_needed'
            confidence = 0.9
        else:
            intent = 'normal_chat'
            confidence = 0.8
        
        return {
            'intent': intent,
            'confidence': confidence,
            'details': {
                'is_short': is_short,
                'needs_rephrase': is_short,  # Will be modified by level logic
                'help_type': help_type,
                'response_type': response_type
            }
        }
    
    def _check_help_patterns(self, message: str, language: str) -> Tuple[bool, str]:
        """Check if message matches help patterns"""
        # Check language-specific patterns
        patterns = self.HELP_PATTERNS.get(language.lower(), [])
        patterns.extend(self.HELP_PATTERNS['english'])  # Always include English
        
        for pattern in patterns:
            if re.search(pattern, message, re.IGNORECASE):
                # Determine help type
                if any(word in message for word in ['translate', 'traducir', 'traduire']):
                    return True, 'translation'
                elif any(word in message for word in ['mean', 'significa', 'bedeutet']):
                    return True, 'explanation'
                else:
                    return True, 'general'
        
        return False, None
    
    def _check_response_type(self, message: str) -> str:
        """Categorize short responses"""
        for response_type, patterns in self.SHORT_RESPONSES.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    return response_type
        return None
    
    def should_check_errors(self, message: str, level: str) -> bool:
        """Determine if we need to check for errors based on level"""
        if level == 'advanced':
            return True  # Always check for advanced
        elif level == 'intermediate':
            return len(message.split()) > 5  # Check longer responses
        else:  # beginner
            return False  # Don't check, always rephrase anyway