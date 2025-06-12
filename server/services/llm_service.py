import openai
from flask import current_app

class LLMService:
    def __init__(self):
        self._openai_client = None
    
    @property
    def openai_client(self):
        """Lazy initialization of OpenAI client"""
        if self._openai_client is None:
            api_key = current_app.config.get('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            self._openai_client = openai.OpenAI(api_key=api_key)
        return self._openai_client
    
    def generate_chat_response(self, messages, temperature=0.3, max_tokens=150):
        """Generate chat response using GPT-4"""
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()
    
    def generate_summary(self, conversation_text):
        """Generate conversation summary"""
        summary_prompt = f"""Please create a concise bullet-point summary of this conversation between a language learner and AI tutor. Focus on:
- Key personal information shared by the user
- Topics discussed
- Language learning progress or challenges
- Important facts to remember for future conversations

Conversation:
{conversation_text}

Provide the summary as bullet points:"""

        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates concise conversation summaries."},
                {"role": "user", "content": summary_prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()