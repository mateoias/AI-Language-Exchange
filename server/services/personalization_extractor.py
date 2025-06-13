import openai
from flask import current_app
import json
import logging

logger = logging.getLogger(__name__)

class PersonalizationExtractor:
    def __init__(self):
        self.client = openai.OpenAI(api_key=current_app.config['OPENAI_API_KEY'])
    
    def extract_from_form(self, user_id, form_data):
        """Extract entities and relationships from personalization form"""
        try:
            # Convert form data to text
            form_text = self._form_to_text(form_data)
            
            # Create extraction prompt
            prompt = self._create_extraction_prompt(user_id, form_text)
            
            # Call OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured information from conversations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            # Parse response
            response_text = response.choices[0].message.content
            
            # Clean response if it contains markdown
            cleaned_response = self._clean_llm_response(response_text)
            
            # Parse JSON
            try:
                extracted_info = json.loads(cleaned_response)
                logger.info(f"Extracted {len(extracted_info.get('entities', []))} entities for user {user_id}")
                return extracted_info
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse extraction response: {e}")
                logger.error(f"Response was: {cleaned_response}")
                return None
                
        except Exception as e:
            logger.error(f"Error in extraction: {str(e)}")
            return None
    
    def _form_to_text(self, form_data):
        """Convert form data to readable text"""
        lines = []
        for key, value in form_data.items():
            if value:
                lines.append(f"My {key} is {value}")
        return "\n".join(lines)
    
    def _create_extraction_prompt(self, user_id, form_text):
        """Create the extraction prompt"""
        return f"""You are a graph database analyst for a language learning app. Analyze this conversation between a user and language tutor to extract meaningful information about the user that should be stored in a knowledge graph.

FOCUS ON:
- Personal facts (family, pets, location, work, hobbies)
- Preferences (likes, dislikes, wants)
- Experiences (places visited, activities done)
- Relationships (knows people, has things)

EXTRACT ONLY information that is:
1. Explicitly stated by the USER (not the tutor)
2. Factual (not opinions about language learning)
3. Useful for future personalized conversations

USER ID: {user_id}
CONVERSATION:
{form_text}

Return ONLY a JSON object (no markdown, no code blocks, no explanatory text) with this exact structure:
{{
  "entities": [
    {{"text": "entity_name", "type": "Person|Place|Animal|Activity|Thing", "context": "brief context"}}
  ],
  "relationships": [
    {{"subject": "user", "predicate": "HAS|LIKES|LIVES_IN|WORKS_AS|KNOWS|VISITED|WANTS", "object": "entity_name", "confidence": "high|medium|low"}}
  ],
  "reasoning": "Brief explanation of what you extracted and why"
}}

If no meaningful information found, return empty arrays."""
    
    def _clean_llm_response(self, response):
        """Remove markdown formatting from LLM response"""
        # Remove markdown code blocks
        if '```json' in response:
            response = response.split('```json')[1].split('```')[0]
        elif '```' in response:
            response = response.split('```')[1].split('```')[0]
        
        # Remove any text before the first {
        if '{' in response:
            response = response[response.index('{'):]
        
        # Remove any text after the last }
        if '}' in response:
            response = response[:response.rindex('}')+1]
        
        return response.strip()