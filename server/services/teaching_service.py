# server/services/teaching_service.py
"""
Service for all teaching interactions (rephrasing and explanations)
Replaces and extends RephraseService
"""
from .llm_manager import llm_manager
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class TeachingService:
    """
    Handles both rephrasing (conversation repair) and direct teaching
    """
    
    def generate_rephrase(
        self,
        user_message: str,
        conversation_context: Dict,
        language: str,
        level: str
    ) -> Optional[str]:
        """
        Rephrase user's short/incorrect response into proper sentence
        Teacher persona, speaking target language
        """
        last_bot_message = conversation_context.get('last_bot_message', '')
        
        system_prompt = f"""You are a friendly {language} teacher (female persona).
Your task is to rephrase the student's response into a complete, correct sentence.

Rules:
1. Speak in {language} (the target language)
2. Make it a natural, complete sentence
3. Keep the student's intended meaning
4. Use second person (tú/vous/du) - "You want..." not "I want..."
5. Be encouraging and natural
6. Maximum 20 words

Level: {level}
- Beginner: Simple vocabulary
- Intermediate: Natural phrasing
- Advanced: Sophisticated expression"""

        user_prompt = f"""Previous question: "{last_bot_message}"
Student said: "{user_message}"

Rephrase this into a complete {language} sentence."""

        try:
            response = llm_manager.generate_chat_response(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=50
            )
            return response.strip()
        except Exception as e:
            logger.error(f"Rephrase generation failed: {e}")
            return None
    
    def generate_explanation(
        self,
        teaching_request: str,
        user_data: Dict,
        conversation_context: Dict
    ) -> str:
        """
        Generate teaching explanation in user's native language
        Teacher persona explaining grammar/vocabulary
        """
        native_lang = user_data['nativeLanguage']
        learning_lang = user_data['learningLanguage']
        
        system_prompt = f"""You are a helpful {learning_lang} teacher (female persona).
Explain things clearly in {native_lang} (the student's native language).

Rules:
1. Answer in {native_lang}
2. Be clear and concise
3. Give practical examples
4. Maximum 2-3 sentences
5. Focus on what helps them continue the conversation"""

        user_prompt = f"""Student learning {learning_lang} asks: "{teaching_request}"

Provide a brief, helpful explanation."""

        try:
            response = llm_manager.generate_chat_response(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )
            return response.strip()
        except Exception as e:
            logger.error(f"Explanation generation failed: {e}")
            return f"I can help with that. Let me explain..."
    
    def generate_repair(
        self,
        user_message: str,
        repair_type: str,
        user_data: Dict,
        conversation_context: Dict
    ) -> str:
        """
        Generate conversation repair (wrong language, unclear, etc)
        Teacher persona, speaking target language
        """
        learning_lang = user_data['learningLanguage']
        native_lang = user_data['nativeLanguage']
        
        repair_prompts = {
            'wrong_language': f"Respond in {learning_lang} asking them to practice in {learning_lang}",
            'unclear': f"Ask for clarification about what they mean",
            'error': f"Gently correct and ask them to try again"
        }
        
        system_prompt = f"""You are a patient {learning_lang} teacher (female persona).
The student made a mistake or needs guidance.

Respond in {learning_lang} to guide them back on track.
Be encouraging and helpful.
Maximum 2 sentences."""

        user_prompt = f"""Student said: "{user_message}"
Problem: {repair_prompts.get(repair_type, 'Help them continue')}

Guide them gently in {learning_lang}."""

        try:
            response = llm_manager.generate_chat_response(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                max_tokens=80
            )
            return response.strip()
        except Exception as e:
            logger.error(f"Repair generation failed: {e}")
            return "¿Puedes repetir eso?"  # Fallback