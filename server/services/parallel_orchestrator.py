# server/services/parallel_orchestrator.py
"""
Parallel Response Orchestrator with Flask Context Support
Manages concurrent generation of teacher and partner responses
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
import time
import logging
from flask import current_app
from functools import partial

logger = logging.getLogger(__name__)

class ParallelOrchestrator:
    """
    Orchestrates parallel generation of responses and intelligently combines them
    """
    _shared_executor = None  # Class-level shared executor
    
    def __init__(self, rephrase_service, response_service, audio_queue_service):
        self.rephrase_service = rephrase_service
        self.response_service = response_service
        self.audio_queue_service = audio_queue_service
        # Use a shared executor to avoid shutdown issues
        if ParallelOrchestrator._shared_executor is None:
            ParallelOrchestrator._shared_executor = ThreadPoolExecutor(max_workers=3)
        self.executor = ParallelOrchestrator._shared_executor
    
    def _run_with_app_context(self, app, func, *args, **kwargs):
        """Run a function with Flask app context"""
        with app.app_context():
            return func(*args, **kwargs)
    
    def generate_parallel_response(
        self,
        user_message: str,
        user_data: Dict,
        conversation_context: Dict,
        intent_data: Dict,
        should_rephrase: bool,
        audio_speed: float = 0.8
    ) -> Dict:
        """
        Generate responses in parallel and return segments as they complete
        
        Returns a dict with:
        - segments: List of response segments
        - generation_times: Dict of timing information
        - strategy_used: Description of the strategy
        """
        # Capture the Flask app instance
        app = current_app._get_current_object()
        
        start_time = time.time()
        generation_times = {}
        
        # Determine strategy based on intent
        strategy = self._determine_strategy(intent_data, should_rephrase)
        logger.info(f"Using strategy: {strategy}")
        
        if strategy == "help_only":
            # Native language question - only teacher responds
            return self._generate_help_only(
                user_message, user_data, conversation_context, 
                intent_data, audio_speed, generation_times
            )
        
        elif strategy == "parallel_with_hint":
            # Target language with potential correction
            return self._generate_parallel_with_hint(
                app, user_message, user_data, conversation_context,
                intent_data, should_rephrase, audio_speed, generation_times
            )
        
        else:  # "normal_conversation"
            # No correction needed, just conversation
            return self._generate_normal_conversation(
                user_message, user_data, conversation_context,
                intent_data, audio_speed, generation_times
            )
    
    def _determine_strategy(self, intent_data: Dict, should_rephrase: bool) -> str:
        """Determine which generation strategy to use"""
        if intent_data['intent'] == 'help_needed':
            return "help_only"
        elif should_rephrase:
            return "parallel_with_hint"
        else:
            return "normal_conversation"
    
    def _generate_help_only(
        self, user_message: str, user_data: Dict, 
        conversation_context: Dict, intent_data: Dict,
        audio_speed: float, generation_times: Dict
    ) -> Dict:
        """Generate only teacher help response"""
        segments = []
        
        # Generate help response
        help_start = time.time()
        help_response = self.response_service._generate_help_text(
            user_message,
            user_data,
            intent_data['details']['help_type']
        )
        generation_times['help'] = time.time() - help_start
        
        segments.append({
            'type': 'help',
            'text': help_response,
            'timing': 0,
            'persona': 'teacher'
        })
        
        # Generate audio for help in native language
        segments_with_audio = self.audio_queue_service.generate_audio_segments(
            segments,
            user_data['learningLanguage'],
            audio_speed,
            user_data['nativeLanguage']
        )
        
        return {
            'segments': segments_with_audio,
            'generation_times': generation_times,
            'strategy_used': 'help_only'
        }
    
    def _generate_parallel_with_hint(
        self, app, user_message: str, user_data: Dict,
        conversation_context: Dict, intent_data: Dict,
        should_rephrase: bool, audio_speed: float,
        generation_times: Dict
    ) -> Dict:
        """Generate rephrase and conversation in parallel with context sharing"""
        segments = []
        futures = {}
        
        # Create shared context hint
        context_hint = self._create_context_hint(user_message, intent_data)
        
        # Submit parallel tasks with Flask context
        try:
            # Start rephrase generation
            if should_rephrase:
                rephrase_start = time.time()
                futures['rephrase'] = self.executor.submit(
                    self._run_with_app_context,
                    app,
                    self.rephrase_service.generate_rephrase,
                    user_message,
                    conversation_context,
                    user_data['learningLanguage'],
                    intent_data['details']
                )
            
            # Start conversation generation WITH HINT about potential correction
            conv_start = time.time()
            futures['conversation'] = self.executor.submit(
                self._run_with_app_context,
                app,
                self._generate_hinted_response,
                user_message,
                user_data,
                conversation_context,
                context_hint
            )
            
            # Process results as they complete
            for future_name, future in futures.items():
                try:
                    result = future.result(timeout=3.0)  # 3 second timeout
                    
                    if future_name == 'rephrase' and result:
                        generation_times['rephrase'] = time.time() - rephrase_start
                        segments.append({
                            'type': 'rephrase',
                            'text': result,
                            'timing': 0,
                            'persona': 'teacher'
                        })
                    
                    elif future_name == 'conversation':
                        generation_times['conversation'] = time.time() - conv_start
                        segments.append({
                            'type': 'response',
                            'text': result['response'],
                            'timing': len(segments) * 800,
                            'persona': 'partner'
                        })
                        
                except Exception as e:
                    logger.error(f"Error in {future_name} generation: {e}")
                    # If parallel generation fails, fall back to sequential
                    if future_name == 'conversation':
                        # Generate conversation response normally
                        result = self.response_service._generate_chat_response(
                            user_message,
                            user_data,
                            conversation_context
                        )
                        segments.append({
                            'type': 'response',
                            'text': result['response'],
                            'timing': len(segments) * 800,
                            'persona': 'partner'
                        })
        
        except Exception as e:
            logger.error(f"Parallel execution failed: {e}")
            # Fallback to sequential generation
            if should_rephrase:
                result = self.rephrase_service.generate_rephrase(
                    user_message,
                    conversation_context,
                    user_data['learningLanguage'],
                    intent_data['details']
                )
                if result:
                    segments.append({
                        'type': 'rephrase',
                        'text': result,
                        'timing': 0,
                        'persona': 'teacher'
                    })
            
            # Generate conversation
            result = self.response_service._generate_chat_response(
                user_message,
                user_data,
                conversation_context
            )
            segments.append({
                'type': 'response',
                'text': result['response'],
                'timing': len(segments) * 800,
                'persona': 'partner'
            })
        
        # Generate audio for all segments in parallel
        segments_with_audio = self.audio_queue_service.generate_audio_segments(
            segments,
            user_data['learningLanguage'],
            audio_speed,
            user_data['nativeLanguage']
        )
        
        return {
            'segments': segments_with_audio,
            'generation_times': generation_times,
            'strategy_used': 'parallel_with_hint'
        }
    
    def _generate_normal_conversation(
        self, user_message: str, user_data: Dict,
        conversation_context: Dict, intent_data: Dict,
        audio_speed: float, generation_times: Dict
    ) -> Dict:
        """Generate normal conversation response without correction"""
        segments = []
        
        # Generate conversation response
        conv_start = time.time()
        response_data = self.response_service._generate_chat_response(
            user_message,
            user_data,
            conversation_context
        )
        generation_times['conversation'] = time.time() - conv_start
        
        segments.append({
            'type': 'response',
            'text': response_data['response'],
            'timing': 0,
            'persona': 'partner'
        })
        
        # Generate audio
        segments_with_audio = self.audio_queue_service.generate_audio_segments(
            segments,
            user_data['learningLanguage'],
            audio_speed
        )
        
        return {
            'segments': segments_with_audio,
            'generation_times': generation_times,
            'strategy_used': 'normal_conversation'
        }
    
    def _create_context_hint(self, user_message: str, intent_data: Dict) -> Dict:
        """Create a hint about what the user likely meant"""
        hint = {
            'original_message': user_message,
            'is_short': intent_data['details']['is_short'],
            'response_type': intent_data['details'].get('response_type')
        }
        
        # Add common correction patterns
        if intent_data['details']['is_short']:
            if intent_data['details'].get('response_type') == 'affirmative':
                hint['likely_meaning'] = 'agreement/confirmation'
            elif intent_data['details'].get('response_type') == 'negative':
                hint['likely_meaning'] = 'disagreement/negation'
        
        return hint
    
    def _generate_hinted_response(
        self, user_message: str, user_data: Dict,
        conversation_context: Dict, context_hint: Dict
    ) -> Dict:
        """Generate response with hint about potential corrections"""
        # Enhanced response generation for parallel context
        
        # For short responses, we can make assumptions
        if context_hint.get('is_short') and context_hint.get('response_type'):
            # Use the enhanced response service method
            return self.response_service.generate_response_with_hint(
                user_message,
                user_data,
                conversation_context,
                context_hint
            )
        else:
            # Regular response generation
            return self.response_service._generate_chat_response(
                user_message,
                user_data,
                conversation_context
            )
    
    def cleanup(self):
        """Cleanup executor - NO LONGER SHUTS DOWN since we use shared executor"""
        # Don't shutdown the shared executor
        pass
    