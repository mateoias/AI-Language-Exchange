# services/llm_manager.py
"""
Centralized LLM Manager for OpenAI client
Singleton pattern to ensure only one client instance exists
"""
import openai
from flask import current_app
from typing import Optional, List, Dict


class LLMManager:
    """
    Centralized manager for LLM operations.
    Uses singleton pattern to ensure only one OpenAI client exists.
    """
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMManager, cls).__new__(cls)
        return cls._instance
    
    @property
    def client(self):
        """Get or create the OpenAI client"""
        if self._client is None:
            api_key = current_app.config.get('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            self._client = openai.OpenAI(api_key=api_key)
        return self._client
    
    def generate_chat_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gpt-4",
        temperature: float = 0.3,
        max_tokens: int = 150
    ) -> str:
        """
        Generate a chat response using the OpenAI API
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: The model to use (default: gpt-4)
            temperature: Controls randomness (0-1)
            max_tokens: Maximum tokens in response
            
        Returns:
            The generated response text
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating chat response: {e}")
            raise
    
    def generate_summary(self, conversation_text: str, max_tokens: int = 200) -> str:
        """
        Generate a conversation summary
        
        Args:
            conversation_text: The conversation to summarize
            max_tokens: Maximum tokens for summary
            
        Returns:
            The generated summary
        """
        summary_prompt = f"""Please create a concise bullet-point summary of this conversation between a language learner and AI tutor. Focus on:
- Key personal information shared by the user
- Topics discussed  
- Language learning progress or challenges
- Important facts to remember for future conversations

Conversation:
{conversation_text}

Provide the summary as bullet points:"""

        messages = [
            {"role": "system", "content": "You are a helpful assistant that creates concise conversation summaries."},
            {"role": "user", "content": summary_prompt}
        ]
        
        return self.generate_chat_response(
            messages=messages,
            temperature=0.3,
            max_tokens=max_tokens
        )
    
    def generate_structured_response(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 1000,
        response_format: str = "json"
    ) -> str:
        """
        Generate a structured response (useful for graph analysis, etc.)
        
        Args:
            system_prompt: System message for context
            user_prompt: The user's prompt
            temperature: Controls randomness (0-1)
            max_tokens: Maximum tokens in response
            response_format: Expected format (json, text, etc.)
            
        Returns:
            The generated response
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.generate_chat_response(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def generate_structured_response(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 1000,
        response_format: str = "json"
    ) -> str:
        """
        Generate a structured response (useful for graph analysis, etc.)
        
        Args:
            system_prompt: System message for context
            user_prompt: The user's prompt
            temperature: Controls randomness (0-1)
            max_tokens: Maximum tokens in response
            response_format: Expected format (json, text, etc.)
            
        Returns:
            The generated response
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.generate_chat_response(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def reset_client(self):
        """Reset the client (useful for testing or config changes)"""
        self._client = None


# Create a global instance
llm_manager = LLMManager()