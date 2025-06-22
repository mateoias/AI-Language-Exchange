# services/prompt_builder.py
"""
Prompt builder service that creates CI/TPRS prompts for language learning
Now uses YAML-based configuration with hot-reload
"""
from typing import Dict, Tuple, List, Optional
from datetime import datetime
from .prompt_loader import prompt_loader
import logging

logger = logging.getLogger(__name__)

class PromptBuilder:
    """
    Builds prompts for the language learning chatbot using CI/TPRS principles
    Loads prompts from YAML configuration files
    """
    
    def __init__(self):
        """Initialize the prompt builder"""
        # Ensure prompt loader is initialized
        if not prompt_loader.prompts_dir:
            prompt_loader.initialize()
    
    def build_prompt(
        self, 
        user_data: Dict, 
        conversation_context: Dict,
        current_message: str,
        mode: str = 'chat',
        reminder_id: str = 'default'
    ) -> Tuple[str, str]:
        """
        Build a prompt based on user data and conversation context
        
        Args:
            user_data: User information including language preferences and level
            conversation_context: Current conversation state and history
            current_message: The user's current message
            mode: Type of interaction ('chat', 'first_meeting', etc.)
            reminder_id: Which reminder to use (default: 'default')
            
        Returns:
            Tuple of (prompt, level)
        """
        # Get level from user data (will come from frontend)
        level = user_data.get('proficiencyLevel', 'beginner').lower()
        
        # Get the appropriate prompt configuration
        level_config = prompt_loader.get_level_prompt(level)
        if not level_config:
            logger.warning(f"No prompt found for level {level}, falling back to beginner")
            level = 'beginner'
            level_config = prompt_loader.get_level_prompt(level)
        
        # Get base template
        base_template = prompt_loader.get_base_template()
        if not base_template:
            logger.error("No base template found!")
            return self._get_fallback_prompt(user_data, conversation_context), level
        
        # Get reminder
        reminder = prompt_loader.get_reminder(reminder_id)
        
        # Build the prompt variables
        prompt_vars = self._build_prompt_variables(
            user_data, 
            conversation_context,
            level_config,
            reminder,
            mode
        )
        
        # Format the template
        try:
            prompt = base_template.format(**prompt_vars)
        except KeyError as e:
            logger.error(f"Missing variable in prompt template: {e}")
            return self._get_fallback_prompt(user_data, conversation_context), level
        
        return prompt, level
    
    
    def _build_prompt_variables(
        self, 
        user_data: Dict, 
        conversation_context: Dict,
        level_config: Dict,
        reminder: str,
        mode: str
    ) -> Dict[str, str]:
        """Build variables to fill in the prompt template"""
        variables = {
            'username': user_data.get('username', 'Student'),
            'native_language': user_data.get('nativeLanguage', 'English'),
            'learning_language': user_data.get('learningLanguage', 'Spanish'),
            'level': level_config.get('level', 'beginner'),
        }
        
        # Get level-specific content
        if mode == 'first_meeting' and 'first_meeting_variant' in level_config:
            variables['base_instruction'] = level_config.get('first_meeting_variant', '')
            variables['level_specific_instruction'] = ''
        else:
            variables['base_instruction'] = level_config.get('base_instruction', '')
            variables['level_specific_instruction'] = level_config.get('level_specific_instruction', '')
        
        variables['level_guidelines'] = level_config.get('level_guidelines', '')
        
        # Add personalization (simplified for now)
        personalization = user_data.get('personalization', {})
        if personalization:
            variables['personalization_section'] = self._format_personalization(personalization)
        else:
            variables['personalization_section'] = ''
        
        # Format conversation history with chunk summaries
        recent_history = self._format_conversation_history(
            conversation_context.get('recent_messages', [])
        )
        
        chunk_summaries = self._format_chunk_summaries(
            conversation_context.get('chunk_summaries', [])
        )
        
        variables['conversation_context'] = chunk_summaries + recent_history
        
        variables['reminder'] = reminder
        
        return variables

    def _format_personalization(self, personalization: Dict) -> str:
        """Format personalization data for inclusion in prompt"""
        # For now, just include a few key items
        # This will be replaced by the personalization selector later
        items = []
        
        if personalization.get('currentLocation'):
            items.append(f"- Location: {personalization['currentLocation']}")
        if personalization.get('workStudy'):
            items.append(f"- Work/Study: {personalization['workStudy']}")
        if personalization.get('hobbies'):
            items.append(f"- Interests: {personalization['hobbies']}")
            
        if items:
            return "User Context:\n" + "\n".join(items)
        return ""
    
    def _format_conversation_history(self, messages: List[Dict]) -> str:
        """Format recent messages for inclusion in prompt"""
        if not messages:
            return "\nThis is the start of your conversation."
        
        # Use all messages provided (up to 10 from conversation_service)
        formatted = ["\nRecent conversation:"]
        
        for i, msg in enumerate(messages):
            sender = msg['sender'].capitalize()
            # Add relative position for context
            position = len(messages) - i  # countdown from most recent
            formatted.append(f"[{position} messages ago] {sender}: {msg['content']}")
        
        # Add a separator before current interaction
        formatted.append("\n[Current message]")
        
        return '\n'.join(formatted)
    
    def _format_chunk_summaries(self, chunk_summaries: List[Dict]) -> str:
        """Format chunk summaries for prompt inclusion"""
        if not chunk_summaries:
            return ""
        
        formatted = ["\nPrevious conversation context:"]
        for summary in chunk_summaries:
            formatted.append(f"[Messages {summary['message_range']}]: {summary['summary']}")
        
        return '\n'.join(formatted)

    def _get_fallback_prompt(self, user_data: Dict, conversation_context: Dict) -> str:
        """Fallback prompt if YAML loading fails"""
        return f"""You are a language tutor helping {user_data.get('username', 'the student')} 
learn {user_data.get('learningLanguage', 'a new language')}. 
Keep responses simple and encouraging. Always respond in {user_data.get('learningLanguage', 'the target language')}."""