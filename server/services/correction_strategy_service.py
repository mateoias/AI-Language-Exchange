# server/services/correction_strategy_service.py
"""
Correction Strategy Service
Decides how to handle different types of errors
"""
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class CorrectionStrategyService:
    """
    Determines the best strategy for correcting errors based on:
    - Error type and severity
    - User proficiency level
    - Correction frequency settings
    - Pedagogical best practices
    """
    
    def __init__(self):
        self.correction_strategies = {
            'context_confusion': {
                'beginner': 'explicit_clarification',
                'intermediate': 'gentle_clarification',
                'advanced': 'subtle_recast'
            },
            'grammar': {
                'beginner': 'full_recast',
                'intermediate': 'partial_recast',
                'advanced': 'metalinguistic_hint'
            },
            'pronunciation': {
                'beginner': 'model_correct',
                'intermediate': 'contrast_incorrect_correct',
                'advanced': 'self_correction_prompt'
            }
        }
    
    def determine_correction_strategy(
        self,
        error_data: Dict,
        user_data: Dict,
        conversation_context: Dict,
        correction_settings: Dict
    ) -> Dict:
        """
        Determine the best correction strategy
        
        Returns:
            {
                'strategy': str,
                'should_correct': bool,
                'correction_type': str,
                'teacher_response': Optional[str],
                'partner_hint': Dict,
                'timing': str  # 'immediate', 'delayed', 'none'
            }
        """
        if not error_data.get('has_errors'):
            return {
                'strategy': 'no_correction',
                'should_correct': False,
                'correction_type': 'none',
                'teacher_response': None,
                'partner_hint': {},
                'timing': 'none'
            }
        
        # Get user settings
        level = user_data.get('proficiencyLevel', 'beginner').lower()
        correction_frequency = correction_settings.get('frequency', 50)  # 0-100
        
        # Check recent correction count
        recent_corrections = self._count_recent_corrections(conversation_context)
        
        # Determine if we should correct
        should_correct = self._should_correct(
            error_data,
            correction_frequency,
            recent_corrections,
            level
        )
        
        if not should_correct:
            # Even if not correcting, provide hint to partner
            return {
                'strategy': 'ignore_with_hint',
                'should_correct': False,
                'correction_type': 'none',
                'teacher_response': None,
                'partner_hint': self._create_partner_hint(error_data),
                'timing': 'none'
            }
        
        # Determine correction strategy based on error type
        main_error_type = error_data['error_types'][0] if error_data['error_types'] else 'general'
        strategy = self._select_strategy(main_error_type, level, error_data)
        
        # Generate correction response
        correction_response = self._generate_correction_response(
            strategy,
            error_data,
            user_data,
            conversation_context
        )
        
        return correction_response
    
    def _should_correct(
        self,
        error_data: Dict,
        correction_frequency: int,
        recent_corrections: int,
        level: str
    ) -> bool:
        """Decide whether to correct based on multiple factors"""
        
        # Always correct major errors
        if error_data['error_severity'] == 'major':
            return True
        
        # Check correction frequency setting
        if correction_frequency == 0:
            return False
        elif correction_frequency == 100:
            return True
        
        # Avoid correction fatigue
        if recent_corrections >= 2:
            # Only correct if major error or high frequency setting
            return error_data['error_severity'] == 'major' or correction_frequency > 80
        
        # Level-based decision
        if level == 'beginner':
            # Beginners need more correction for learning
            return correction_frequency > 30
        elif level == 'intermediate':
            # Intermediate: correct if frequency > 50 or confidence high
            return correction_frequency > 50 or error_data.get('confidence', 0) > 0.8
        else:  # advanced
            # Advanced: only correct clear errors
            return error_data.get('confidence', 0) > 0.85
    
    def _select_strategy(
        self,
        error_type: str,
        level: str,
        error_data: Dict
    ) -> str:
        """Select appropriate correction strategy"""
        
        # Special handling for context confusion (libro/Liverpool)
        if error_type == 'context_confusion':
            if level == 'beginner':
                return 'explicit_clarification'
            else:
                return 'gentle_clarification'
        
        # Grammar errors
        elif error_type == 'grammar':
            if level == 'beginner':
                return 'full_recast'
            elif level == 'intermediate':
                return 'partial_recast'
            else:
                return 'metalinguistic_hint'
        
        # Default strategy
        return 'gentle_correction'
    
    def _generate_correction_response(
        self,
        strategy: str,
        error_data: Dict,
        user_data: Dict,
        conversation_context: Dict
    ) -> Dict:
        """Generate the actual correction response based on strategy"""
        
        language = user_data['learningLanguage']
        main_correction = error_data['corrections'][0] if error_data['corrections'] else {}
        
        response = {
            'strategy': strategy,
            'should_correct': True,
            'correction_type': strategy,
            'timing': 'immediate'
        }
        
        # Generate teacher response based on strategy
        if strategy == 'explicit_clarification':
            # Direct but friendly clarification
            if main_correction.get('reason') == 'phonetic_confusion':
                response['teacher_response'] = self._generate_clarification(
                    main_correction['original'],
                    main_correction['suggested'],
                    language
                )
            else:
                response['teacher_response'] = f"Did you mean '{main_correction['suggested']}'?"
                
        elif strategy == 'gentle_clarification':
            # Softer clarification
            response['teacher_response'] = self._generate_gentle_clarification(
                main_correction,
                language
            )
            
        elif strategy == 'full_recast':
            # Complete rephrasing
            response['teacher_response'] = self._generate_full_recast(
                error_data,
                conversation_context,
                language
            )
            
        elif strategy == 'partial_recast':
            # Partial rephrasing focusing on error
            response['teacher_response'] = self._generate_partial_recast(
                main_correction,
                language
            )
            
        elif strategy == 'metalinguistic_hint':
            # Grammar explanation
            response['teacher_response'] = self._generate_metalinguistic_hint(
                main_correction,
                language
            )
        
        # Always include partner hint
        response['partner_hint'] = self._create_partner_hint_with_correction(
            error_data,
            main_correction,
            strategy
        )
        
        return response
    
    def _generate_clarification(
        self,
        original: str,
        suggested: str,
        language: str
    ) -> str:
        """Generate clarification for confused terms"""
        if language.lower() == 'spanish':
            if original == 'libro' and suggested.lower() == 'liverpool':
                return f"Ah, ¿te refieres a {suggested}, el equipo de fútbol?"
            else:
                return f"¿Quisiste decir '{suggested}'?"
        else:
            return f"Did you mean '{suggested}'?"
    
    def _generate_gentle_clarification(
        self,
        correction: Dict,
        language: str
    ) -> str:
        """Generate gentle clarification"""
        if language.lower() == 'spanish':
            if correction['reason'] == 'phonetic_confusion':
                return f"Creo que te refieres a {correction['suggested']}, ¿verdad?"
            else:
                return f"Ah, {correction['suggested']}... ¡entiendo!"
        else:
            return f"Oh, you mean {correction['suggested']}... got it!"
    
    def _generate_full_recast(
        self,
        error_data: Dict,
        conversation_context: Dict,
        language: str
    ) -> str:
        """Generate full recast of the sentence"""
        # This would use the rephrase service
        # For now, return a simple recast
        correction = error_data['corrections'][0]
        return correction.get('suggested', '')
    
    def _generate_partial_recast(
        self,
        correction: Dict,
        language: str
    ) -> str:
        """Generate partial recast focusing on the error"""
        if language.lower() == 'spanish':
            return f"...{correction['suggested']}..."
        else:
            return f"...{correction['suggested']}..."
    
    def _generate_metalinguistic_hint(
        self,
        correction: Dict,
        language: str
    ) -> str:
        """Generate grammar explanation"""
        if correction.get('explanation'):
            return correction['explanation']
        return "Remember the grammar rule here."
    
    def _count_recent_corrections(self, conversation_context: Dict) -> int:
        """Count corrections in recent messages"""
        recent_messages = conversation_context.get('recent_messages', [])
        correction_count = 0
        
        # Look for teacher persona messages in last 10 messages
        for msg in recent_messages[-10:]:
            if msg['sender'] == 'bot' and msg.get('message_type') in ['rephrase', 'correction']:
                correction_count += 1
                
        return correction_count
    
    def _create_partner_hint(self, error_data: Dict) -> Dict:
        """Create hint for partner even when not correcting"""
        if not error_data['corrections']:
            return {}
            
        main_correction = error_data['corrections'][0]
        return {
            'has_error': True,
            'likely_meant': main_correction.get('suggested', ''),
            'error_type': main_correction.get('reason', ''),
            'ignore_error': True
        }
    
    def _create_partner_hint_with_correction(
        self,
        error_data: Dict,
        main_correction: Dict,
        strategy: str
    ) -> Dict:
        """Create hint for partner when correcting"""
        return {
            'has_error': True,
            'likely_meant': main_correction.get('suggested', ''),
            'error_type': main_correction.get('reason', ''),
            'correction_happening': True,
            'correction_strategy': strategy,
            'continue_assuming_corrected': True
        }