# server/services/error_detection_service.py
"""
Error Detection Service
Analyzes user input for errors in context of conversation
"""
from typing import List, Dict
import json
from .llm_manager import llm_manager
import logging

logger = logging.getLogger(__name__)

class ErrorDetectionService:

    
    def __init__(self):
        self.llm_manager = llm_manager

    
    def detect_errors(
        self, 
        message: str, 
        recent_messages: List[Dict],
        language: str
    ) -> Dict:
        """Use LLM for sophisticated error detection"""
        # Build context
        logger.info(f"recent_messages type: {type(recent_messages)} content: {recent_messages}")

        context_str = ""
        for msg in recent_messages[-4:]:
            context_str += f"{msg['sender'].capitalize()}: {msg['content']}\n"
        
        prompt = f"""You are a {language} language teaching assistant analyzing student errors.

Given this conversation:
{context_str}
Student: {message}

Analyze if the student made any errors considering:
1. Does their response make sense in context?
2. Are there grammar errors?
3. Are there word confusions (using similar sounding wrong words)?
4. Is the meaning clear?

Respond in JSON format:
{{
  "has_errors": true/false,
  "error_severity": "none/minor/major",
  "main_error": "description of main error if any",
  "correction": "suggested correction if needed",
  "explanation": "brief explanation"
}}"""

        try:
            response = self.llm_manager.generate_chat_response(
                messages=[
                    {"role": "system", "content": "You are an expert language teacher. Be strict about errors but understanding."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            # Parse JSON response
            import json
            result = json.loads(response)
            
            if result.get('has_errors'):
                return {
                    'has_errors': True,
                    'error_severity': result.get('error_severity', 'minor'),
                    'error_types': ['llm_detected'],
                    'corrections': [{
                        'original': message,
                        'suggested': result.get('correction', ''),
                        'confidence': 0.7,
                        'reason': 'llm_analysis',
                        'explanation': result.get('explanation', '')
                    }],
                    'confidence': 0.7
                }
                
        except Exception as e:
            logger.error(f"LLM error check failed: {e}")
        
        return {'has_errors': False, 'error_severity': 'none', 'error_types': [], 'corrections': []}
    
