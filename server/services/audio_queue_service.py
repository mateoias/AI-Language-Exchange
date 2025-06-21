# server/services/audio_queue_service.py
"""
Service for managing audio generation queue
"""
from .audio_service import AudioService
from typing import List, Dict, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AudioQueueService:
    """
    Manages parallel audio generation and queueing
    """
    
    def __init__(self, speech_key, speech_region):
        self.audio_service = AudioService(speech_key, speech_region)
        self.executor = ThreadPoolExecutor(max_workers=3)
    
    def generate_audio_segments(
        self,
        segments: List[Dict[str, str]],
        language: str,
        speed: float = 0.8
    ) -> List[Dict[str, any]]:
        """
        Generate audio for multiple segments in parallel
        
        Args:
            segments: List of {'type': str, 'text': str}
            language: Target language
            speed: Audio speed
            
        Returns:
            List of segments with audio_data added
        """
        # Submit all audio generation tasks
        futures = []
        for segment in segments:
            if segment.get('text'):
                future = self.executor.submit(
                    self.audio_service.generate_audio,
                    segment['text'],
                    language,
                    speed
                )
                futures.append((segment, future))
            else:
                futures.append((segment, None))
        
        # Collect results
        results = []
        for segment, future in futures:
            if future:
                try:
                    audio_data = future.result(timeout=5)  # 5 second timeout
                    segment['audio_data'] = audio_data
                except Exception as e:
                    print(f"Audio generation failed for segment: {e}")
                    segment['audio_data'] = None
            
            results.append(segment)
        
        return results
    
    def cleanup(self):
        """Cleanup executor"""
        self.executor.shutdown(wait=True)