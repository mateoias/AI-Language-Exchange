# services/prompt_builder.py
"""
Prompt builder service that creates CI/TPRS prompts for language learning
"""
from typing import Dict, Tuple, List, Optional
from datetime import datetime


class PromptBuilder:
    """
    Builds prompts for the language learning chatbot using CI/TPRS principles
    """
    
    # For now, store prompts here. Later can move to separate config file
    PROMPTS = {
        'beginner': {
            'chat': """You are a friendly language exchange partner helping {username} practice {learning_language}. 

You are using comprehensible input (CI) and TPRS principles to help them learn.

User Details:
- Native Language: {native_language}
- Learning: {learning_language}
- Name: {username}
- Location: {location}
- Work/Study: {work_study}

CI/TPRS Principles for Beginners:
1. Use only high-frequency words (most common 100-200 words)
2. Keep sentences very short (3-7 words maximum)
3. Repeat key words naturally 3-5 times in your response
4. Use cognates when possible
5. Circle back to previous vocabulary from earlier in the conversation
6. If they make an error, recast it correctly without pointing out the mistake

{conversation_history}

Guidelines:
- Always respond in {learning_language}
- If the user makes a mistake or just answers with one word, rephrase their answer correctly with a full sentence in {learning_language}
- Use simple present tense primarily
- ALWAYS ask a simple yes/no or either/or question at the end of each response
- Keep your response under 50 words
- Be encouraging and react with enthusiasm to their attempts

Remember: They need to understand 95%+ of what you say. When in doubt, simplify!""",

            'first_meeting': """You are meeting {username} for the first time to help them learn {learning_language}.

Start with the absolute basics:
- Greet them warmly
- Ask their name (even though you know it)
- React with enthusiasm
- Ask ONE simple either/or question about them
- Use gestures/actions in parentheses to aid comprehension

Use only these basic words/phrases for first interaction:
- Hello/Hi equivalents
- "What is your name?" equivalent  
- "My name is..." equivalent
- "Nice to meet you" equivalent
- Basic adjectives: good, big, small
- Yes/no

Keep it under 30 words total!""",
        },
        
        'intermediate': {
            'chat': """You are a CI/TPRS language teacher helping {username} progress in {learning_language}.

User Profile:
- Native Language: {native_language}
- Learning: {learning_language}
- Level: Intermediate (can handle basic past tense and descriptions)
- Location: {location}
- Interests: {work_study}

{recent_summaries}

CI Principles for Intermediates:
1. Use high-frequency words + common conversational vocabulary
2. Introduce past tense naturally through personal stories
3. Keep sentences moderate length (7-12 words)
4. Ask follow-up questions to encourage elaboration
5. Recast errors naturally in your response
6. Use "¿Por qué?" "¿Cuándo?" "¿Cómo?" type questions

{conversation_history}

Guidelines:
- Respond only in {learning_language}
- Share brief personal anecdotes to model past tense
- Ask open-ended questions that require more than yes/no
- Gradually increase complexity based on their responses
- Keep responses under 75 words
- End with a question that encourages them to use past tense""",
        },
        
        'advanced': {
            'chat': """You are helping {username} achieve fluency in {learning_language} through natural conversation.

User Profile:
- Native Language: {native_language}  
- Learning: {learning_language}
- Level: Advanced
- Professional field: {work_study}

{recent_summaries}

Advanced CI Principles:
1. Natural, authentic conversation at native speed
2. Use idiomatic expressions in context
3. Discuss abstract concepts and current events
4. Model various registers (formal/informal)
5. Introduce 1-2 new expressions naturally per exchange

{conversation_history}

Guidelines:
- Use {learning_language} exclusively
- Engage in substantive discussions about their field
- Challenge with hypotheticals and opinion questions
- Natural conversation flow - no artificial simplification
- Responses can be 100-150 words
- End with thought-provoking questions""",
        }
    }
    
    def __init__(self):
        """Initialize the prompt builder"""
        pass
    
    def build_prompt(
        self, 
        user_data: Dict, 
        conversation_context: Dict,
        current_message: str,
        mode: str = 'chat'
    ) -> Tuple[str, str]:
        """
        Build a prompt based on user data and conversation context
        
        Args:
            user_data: User information including language preferences
            conversation_context: Current conversation state and history
            current_message: The user's current message
            mode: Type of interaction ('chat', 'first_meeting', etc.)
            
        Returns:
            Tuple of (prompt, detected_level)
        """
        # Determine user level
        level = self._determine_level(user_data, conversation_context, current_message)
        
        # Get the appropriate template
        template = self._get_template(level, mode)
        
        # Build the prompt variables
        prompt_vars = self._build_prompt_variables(user_data, conversation_context)
        
        # Format the template
        prompt = template.format(**prompt_vars)
        
        return prompt, level
    
    def _determine_level(
        self, 
        user_data: Dict, 
        conversation_context: Dict,
        current_message: str
    ) -> str:
        """
        Determine user's proficiency level based on various factors
        
        Simple heuristics for now - can be made more sophisticated
        """
        # Check if level is explicitly set in user data
        if user_data.get('proficiencyLevel'):
            return user_data['proficiencyLevel']
        
        # Simple heuristics based on conversation
        message_count = conversation_context.get('message_count', 0)
        avg_message_length = len(current_message.split())
        
        # Check for conversation summaries (indicates multiple sessions)
        has_summaries = len(conversation_context.get('conversation_summaries', [])) > 0
        
        # Very basic level detection
        if message_count < 20 or avg_message_length < 3:
            return 'beginner'
        elif message_count < 100 or not has_summaries:
            return 'intermediate'
        else:
            return 'advanced'
    
    def _get_template(self, level: str, mode: str) -> str:
        """Get the appropriate prompt template"""
        level_prompts = self.PROMPTS.get(level, self.PROMPTS['beginner'])
        
        # Check if this is first interaction
        if mode == 'first_meeting' and level == 'beginner':
            return level_prompts.get('first_meeting', level_prompts['chat'])
        
        return level_prompts.get(mode, level_prompts['chat'])
    
    def _build_prompt_variables(
        self, 
        user_data: Dict, 
        conversation_context: Dict
    ) -> Dict[str, str]:
        """Build variables to fill in the prompt template"""
        # Basic user information
        variables = {
            'username': user_data.get('username', 'Student'),
            'native_language': user_data.get('nativeLanguage', 'English'),
            'learning_language': user_data.get('learningLanguage', 'Spanish'),
        }
        
        # Add personalization data
        personalization = user_data.get('personalization', {})
        variables['location'] = personalization.get('currentLocation', 'Unknown')
        variables['work_study'] = personalization.get('workStudy', 'General interests')
        
        # Format conversation history
        variables['conversation_history'] = self._format_conversation_history(
            conversation_context.get('recent_messages', [])
        )
        
        # Format conversation summaries for context
        variables['recent_summaries'] = self._format_summaries(
            conversation_context.get('conversation_summaries', [])
        )
        
        return variables
    
    def _format_conversation_history(self, messages: List[Dict]) -> str:
        """Format recent messages for inclusion in prompt"""
        if not messages:
            return "\nThis is the start of your conversation."
        
        formatted = ["\nRecent conversation:"]
        for msg in messages[-5:]:  # Last 5 messages
            sender = msg['sender'].capitalize()
            formatted.append(f"{sender}: {msg['content']}")
        
        return '\n'.join(formatted)
    
    def _format_summaries(self, summaries: List[str]) -> str:
        """Format conversation summaries for context"""
        if not summaries:
            return ""
        
        formatted = ["\nPrevious conversation highlights:"]
        for summary in summaries[-2:]:  # Last 2 summaries
            formatted.append(summary)
        
        return '\n'.join(formatted)