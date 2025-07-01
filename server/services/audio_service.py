import azure.cognitiveservices.speech as speechsdk
from flask import current_app
from ..language_config import get_voice_name, get_pause_durations
import base64

class AudioService:
    def __init__(self, speech_key, speech_region):
        self._speech_config = None
        self._audio_cache = {}
        self.speech_key = speech_key
        self.speech_region = speech_region

    
    @property
    def speech_config(self):
        if self._speech_config is None:
            if not self.speech_key or not self.speech_region:
                raise ValueError("Azure Speech credentials not configured")
            self._speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key,
                region=self.speech_region
            )
            self._speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
            )
        return self._speech_config

    
    def _get_voice_name(self, language, voice_type='male', persona=None):
        """Map language to Azure voice name based on persona"""
        # If persona specified, use it to determine voice type
        if persona:
            voice_type = 'female' if persona == 'teacher' else 'male'
        
        return get_voice_name(language, voice_type)
    
    def _add_speech_marks(self, text, speed_rate=1.0, voice_name="en-US-AriaNeural"):
        """Add SSML markup for natural pauses, speed, and voice"""
        prosody_rate = f"{speed_rate:.1f}"
        pauses = get_pause_durations()
        pause_multiplier = 1.0 / speed_rate
        
        sentence_pause = int(pauses['sentence'] * pause_multiplier)
        comma_pause = int(pauses['comma'] * pause_multiplier)
        semicolon_pause = int(pauses['semicolon'] * pause_multiplier)
        
        text = text.replace('.', f'.<break time="{sentence_pause}ms"/>')
        text = text.replace(',', f',<break time="{comma_pause}ms"/>')
        text = text.replace('!', f'!<break time="{sentence_pause}ms"/>')
        text = text.replace('?', f'?<break time="{sentence_pause}ms"/>')
        text = text.replace(';', f';<break time="{semicolon_pause}ms"/>')

        ssml = f'''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <voice name="{voice_name}">
                <prosody rate="{prosody_rate}">
                    {text}
                </prosody>
            </voice>
        </speak>'''
        
        return ssml
    
    def generate_audio(self, text, language, speed_rate=0.8, persona=None):
        """Generate audio using Azure TTS"""
        try:
            cache_key = f"{text}_{language}_{speed_rate}"
            if cache_key in self._audio_cache:
                return self._audio_cache[cache_key]
            
            voice_name = self._get_voice_name(language, persona=persona)
            self.speech_config.speech_synthesis_voice_name = voice_name
            
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=None
            )
            
            ssml_text = self._add_speech_marks(text, speed_rate, voice_name)
            result = synthesizer.speak_ssml_async(ssml_text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                audio_data = result.audio_data
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                self._audio_cache[cache_key] = audio_base64
                return audio_base64
            else:
                print(f"Speech synthesis failed: {result.reason}")
                return None
                
        except Exception as e:
            print(f"Error generating audio: {str(e)}")
            return None
    
    def clear_cache(self):
        """Clear audio cache"""
        self._audio_cache.clear()