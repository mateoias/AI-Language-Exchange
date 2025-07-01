# server/services/parallel_orchestrator.py
"""
Simplified parallel orchestrator for reducing perceived latency
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List
import time
import logging
from flask import current_app

logger = logging.getLogger(__name__)

class ParallelOrchestrator:
    """
    Orchestrates parallel generation of teacher and partner responses
    """
    _shared_executor = None
    
    def __init__(self, teaching_service, response_service, audio_queue_service):
        self.teaching_service = teaching_service
        self.response_service = response_service
        self.audio_queue_service = audio_queue_service
        
        if ParallelOrchestrator._shared_executor is None:
            ParallelOrchestrator._shared_executor = ThreadPoolExecutor(max_workers=2)
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
        analysis: Dict,
        audio_speed: float = 0.8
    ) -> Dict:
        """
        Generate rephrase and response in parallel for beginners
        Returns segments as they complete for reduced perceived latency
        """
        app = current_app._get_current_object()
        segments = []
        futures = {}
        
        # Start rephrase generation immediately if needed
        if analysis['needs_rephrase']:
            futures['rephrase'] = self.executor.submit(
                self._run_with_app_context,
                app,
                self.teaching_service.generate_rephrase,
                user_message,
                conversation_context,
                user_data['learningLanguage'],
                user_data.get('proficiencyLevel', 'beginner')
            )
        
        # Start response generation in parallel
        futures['response'] = self.executor.submit(
            self._run_with_app_context,
            app,
            self.response_service.generate_response,
            user_message,
            user_data,
            conversation_context,
            analysis
        )
        
        # Process results as they complete
        for future_name, future in futures.items():
            try:
                result = future.result(timeout=3.0)
                
                if future_name == 'rephrase' and result:
                    segments.append({
                        'type': 'rephrase',
                        'text': result,
                        'timing': 0,
                        'persona': 'teacher'
                    })
                
                elif future_name == 'response':
                    segments.append({
                        'type': 'response',
                        'text': result['response'],
                        'timing': len(segments) * 800,
                        'persona': 'partner'
                    })
                    
            except Exception as e:
                logger.error(f"Parallel generation error for {future_name}: {e}")
        
        # Generate audio for all segments
        segments_with_audio = self.audio_queue_service.generate_audio_segments(
            segments,
            user_data['learningLanguage'],
            audio_speed,
            user_data['nativeLanguage']
        )
        
        # Add response to conversation
        response_segment = next((s for s in segments if s['type'] == 'response'), None)
        if response_segment:
            self.response_service.conversation_service.add_message(
                user_data['id'],
                response_segment['text'],
                'bot',
                'chat',
                user_data['learningLanguage']
            )
        
        return {
            'segments': segments_with_audio,
            'intent': 'chat',
            'rephrased': analysis['needs_rephrase'],
            'audio_language': user_data['learningLanguage']
        }
    
    def cleanup(self):
        """Cleanup (no longer shuts down shared executor)"""
        pass