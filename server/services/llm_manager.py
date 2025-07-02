# services/llm_manager.py
"""
Centralized LLM Manager for OpenAI client with comprehensive logging
"""
import openai
from flask import current_app
from typing import Optional, List, Dict


class LLMManager:
    """
    Centralized manager for LLM operations with detailed logging
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
        model: str = "gpt-4o",
        temperature: float = 0.3,
        max_tokens: int = 80,
        log_request: bool = False  # New parameter for logging
    ) -> str:
        """
        Generate a chat response using the OpenAI API with optional detailed logging
        """
        
        if log_request:
            # Log the full prompt with nice formatting
            print("\n" + "="*80)
            print(f"🤖 LLM REQUEST - Model: {model}, Temp: {temperature}, Max Tokens: {max_tokens}")
            print("="*80)
            
            for i, message in enumerate(messages):
                role_emoji = "🔧" if message['role'] == 'system' else "👤" if message['role'] == 'user' else "🤖"
                print(f"\n{role_emoji} {message['role'].upper()} MESSAGE #{i+1}:")
                print("-" * 50)
                
                # Truncate very long system prompts for readability
                content = message['content']
                if message['role'] == 'system' and len(content) > 1000:
                    print(content[:500])
                    print(f"\n... [TRUNCATED - Total length: {len(content)} chars] ...")
                    print(content[-200:])
                else:
                    print(content)
            
            print("\n" + "="*80)
        
        try:
            import time
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            result = response.choices[0].message.content.strip()
            
            if log_request:
                print(f"🤖 LLM RESPONSE (took {duration_ms:.0f}ms):")
                print("-" * 50)
                
                # For JSON responses, try to format nicely
                if result.startswith('{') and result.endswith('}'):
                    try:
                        import json
                        formatted_json = json.dumps(json.loads(result), indent=2)
                        print(formatted_json)
                    except:
                        print(result)  # Fallback to raw output
                else:
                    print(result)
                
                print("="*80 + "\n")
            
            return result
            
        except Exception as e:
            if log_request:
                print(f"❌ LLM ERROR: {e}")
                print("="*80 + "\n")
            print(f"Error generating chat response: {e}")
            raise
    
    def generate_summary(self, conversation_text: str, max_tokens: int = 200) -> str:
        """Generate a conversation summary"""
        summary_prompt = f"""Please create a concise bullet-point summary of this conversation between a language learner and AI tutor. Focus on:
- Topics discussed  
- Key personal information shared by the user
- Language learning progress or challenges

Conversation:
{conversation_text}

Provide the summary as bullet points:"""

        messages = [
            {"role": "system", "content": "You are a helpful assistant that creates concise conversation summaries."},
            {"role": "user", "content": summary_prompt}
        ]
        print(messages)
        return self.generate_chat_response(
            messages=messages,
            temperature=0.3,
            max_tokens=max_tokens,
            log_request=False  # Don't log summary generation
        )
    
    def generate_structured_response(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 1000,
        response_format: str = "json"
    ) -> str:
        """Generate a structured response (useful for graph analysis, etc.)"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.generate_chat_response(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            log_request=True if response_format == "json" else False
        )
    
    def reset_client(self):
        """Reset the client (useful for testing or config changes)"""
        self._client = None


# Create a global instance
llm_manager = LLMManager()