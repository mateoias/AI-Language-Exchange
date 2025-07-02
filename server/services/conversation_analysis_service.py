# server/services/conversation_analysis_service.py
"""
Unified service for analyzing user input and determining conversation flow
Replaces: IntentService, ErrorDetectionService, CorrectionStrategyService
"""
from typing import Dict, Tuple, Optional
from .llm_manager import llm_manager
import json
import logging

logger = logging.getLogger(__name__)

class ConversationAnalysisService:
    """
    Fast analysis to determine what type of response is needed
    """
    
    def analyze_message(
        self,
        message: str,
        user_data: Dict,
        conversation_context: Dict
    ) -> Dict:
        """
        Analyze user message to determine flow and needed responses
        
        Returns:
        {
            'flow_type': 'conversation' | 'teaching' | 'repair',
            'needs_rephrase': bool,
            'repair_type': Optional[str],  # 'wrong_language', 'unclear', 'error', 'off-topic'
            'teaching_request': Optional[str],  # what they're asking about
            'confidence': float
        }
        """
        # Quick heuristics first
        quick_result = self._quick_analysis(message, user_data)
        if quick_result['confidence'] > 0.8:
            return quick_result
            
        # LLM analysis for complex cases
        return self._llm_analysis(message, user_data, conversation_context)
    
    def _quick_analysis(self, message: str, user_data: Dict) -> Dict:
        """Quick pattern matching for common cases"""
        message_lower = message.lower().strip()
        learning_lang = user_data['learningLanguage'].lower()
        native_lang = user_data['nativeLanguage'].lower()
        level = user_data.get('proficiencyLevel', 'beginner')
        
        # Teaching patterns (native language questions about target language)
        teaching_patterns = {
            'english': ['what does', 'what is', 'how do you say', 'explain', 'help'],
            'spanish': ['qué significa', 'cómo se dice', 'explica', 'ayuda'],
            # Add more languages as needed
        }
        
        # Check for teaching request
        patterns = teaching_patterns.get(native_lang.lower(), teaching_patterns['english'])
        for pattern in patterns:
            if pattern in message_lower:
                return {
                    'flow_type': 'teaching',
                    'needs_rephrase': False,
                    'repair_type': None,
                    'teaching_request': message,
                    'confidence': 0.9
                }
        
        # Check if message is very short (needs rephrase for beginners)
        word_count = len(message.split())
        if level == 'beginner' and word_count <= 3:
            return {
                'flow_type': 'conversation',
                'needs_rephrase': True,
                'repair_type': None,
                'teaching_request': None,
                'confidence': 0.9
            }
        
        # Default to normal conversation
        return {
            'flow_type': 'conversation',
            'needs_rephrase': False,
            'repair_type': None,
            'teaching_request': None,
            'confidence': 0.5  # Low confidence triggers LLM analysis
        }
    
    def _llm_analysis(
        self,
        message: str,
        user_data: Dict,
        conversation_context: Dict
    ) -> Dict:
        """Use LLM for nuanced analysis"""
        
        # Get recent context
        recent_messages = conversation_context.get('recent_messages', [])[-4:]
        context_str = "\n".join([
            f"{msg['sender']}: {msg['content']}" 
            for msg in recent_messages
        ])
        
        prompt = f"""Analyze this language learning conversation to determine the appropriate response flow.

User is learning: {user_data['learningLanguage']}
User's native language: {user_data['nativeLanguage']}
User's level: {user_data.get('proficiencyLevel', 'beginner')}

Recent conversation:
{context_str}
User: {message}

Determine:
1. Is this a teaching request (asking for help/explanation)?
2. Is this normal conversation that should continue?
3. Does this need repair (wrong language, unclear, unclear, off-topic)?
4. Should we rephrase their response (too short, grammatically incorrect)?

Respond with JSON:
{{
    "flow_type": "conversation|teaching|repair",
    "needs_rephrase": true/false,
    "repair_type": null or "wrong_language|unclear|error|off-topic",
    "teaching_request": null or "what they're asking about",
    "reasoning": "brief explanation"
}}"""

        try:
            response = llm_manager.generate_chat_response(
                messages=[
                    {"role": "system", "content": "You are a language learning analysis system."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            result = json.loads(response)
            result['confidence'] = 1.0
            return result
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            # Fallback to conversation
            return {
                'flow_type': 'conversation',
                'needs_rephrase': False,
                'repair_type': None,
                'teaching_request': None,
                'confidence': 0.3
            }