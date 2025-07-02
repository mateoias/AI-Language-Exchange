# server/services/teaching_service.py

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
        Rephrase user's short/incorrect response into a full correct sentence
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
3. Maximum 2-3 sentences
4. Focus on what helps them continue the conversation"""

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
        
    def generate_follow_up_after_teaching(
        self,
        user_data: Dict,
        conversation_context: Dict,
        teaching_topic: str = None
    ) -> str:
        """
        Generate a follow-up after teaching explanation
        """
        learning_lang = user_data['learningLanguage']
        
        # Get the last conversation topic from context
        recent_messages = conversation_context.get('recent_messages', [])
        last_topic = ""
        
        # Find the last substantive exchange
        for msg in reversed(recent_messages):
            if msg['sender'] == 'bot' and msg.get('content'):
                last_topic = msg['content']
                break
        
        system_prompt = f"""You are a conversation partner (male persona) helping someone learn {learning_lang}.
    The teacher just explained something about: {teaching_topic or 'a language concept'}.
    The last conversation topic was: {last_topic}

    Now continue the conversation naturally in {learning_lang}.

    Rules:
    1. Speak only in {learning_lang}
    2. Reference what was just discussed if relevant
    3. Connect back to the conversation topic naturally
    4. Ask an engaging question to continue
    5. Be encouraging
    6. Maximum 2 sentences"""

        response = llm_manager.generate_chat_response(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Continue the conversation after the explanation"}
            ],
            temperature=0.7,
            max_tokens=80
        )
        
        return response.strip()