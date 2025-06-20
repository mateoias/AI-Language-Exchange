# routes/chat.py
import logging
from io import BytesIO

from flask import Blueprint, request, jsonify, current_app
from ..utils.auth_utils import token_required
from ..services.chat_service import ChatService
from ..services.audio_service import AudioService

chat_bp = Blueprint('chat', __name__)

# Create single service instances
chat_service = ChatService()
audio_service = AudioService()

@chat_bp.route('/message', methods=['POST'])
@token_required
def send_message(user_id):
    """Send a message and get bot response with audio"""
    try:
        data = request.get_json()
        
        if not data or not data.get('message'):
            return jsonify({'error': 'Message content is required'}), 400
        
        message_content = data['message'].strip()
        if not message_content:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Get audio speed preference (default to 0.8 = 80%)
        audio_speed = data.get('audio_speed', 0.8)
        
        # Validate audio speed (between 0.5 and 1.5)
        if not 0.5 <= audio_speed <= 1.5:
            audio_speed = 0.8
        
        # Generate response using persistent service with audio
        result = chat_service.generate_response(user_id, message_content, audio_speed)
        
        if 'error' in result:
            return jsonify({
                'response': result['response'],
                'intent': result['intent'],
                'audio_language': result['audio_language'],
                'audio_data': result.get('audio_data')  # May be None on error
            }), 500
        
        return jsonify({
            'response': result['response'],
            'intent': result['intent'],
            'audio_language': result['audio_language'],
            'audio_data': result['audio_data']
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@chat_bp.route('/history', methods=['GET'])
@token_required
def get_history(user_id):
    """Get conversation history for current session"""
    try:
        history = chat_service.get_conversation_history(user_id)
        return jsonify(history), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@chat_bp.route('/new-session', methods=['POST'])
@token_required
def new_session(user_id):
    """Start a new conversation session"""
    try:
        result = chat_service.start_new_session(user_id)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@chat_bp.route('/regenerate-audio', methods=['POST'])
@token_required
def regenerate_audio(user_id):
    """Regenerate audio for a message with different speed"""
    try:
        data = request.get_json()
        
        if not data or not data.get('text') or not data.get('language'):
            return jsonify({'error': 'Text and language are required'}), 400
        
        text = data['text']
        language = data['language']
        audio_speed = data.get('audio_speed', 0.8)
        
        # Validate audio speed
        if not 0.5 <= audio_speed <= 1.5:
            audio_speed = 0.8
        
        # Generate audio using the audio service
        audio_data = audio_service.generate_audio(text, language, audio_speed)
        
        if audio_data:
            return jsonify({'audio_data': audio_data}), 200
        else:
            return jsonify({'error': 'Failed to generate audio'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@chat_bp.route('/transcribe', methods=['POST'])
@token_required
def transcribe_audio(user_id):
    """Transcribe audio using OpenAI Whisper"""
    try:
        # Check if audio file is in request
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        
        if audio_file.filename == '':
            return jsonify({'error': 'No audio file selected'}), 400
        
        # Get language from form data (optional)
        language = request.form.get('language', None)  # None = auto-detect
        
       # Use Whisper API to transcribe
        try:
            from openai import OpenAI
            client = OpenAI(api_key=current_app.config.get('OPENAI_API_KEY'))
                
                # Read the uploaded file into BytesIO (file-like object)
            audio_bytes = audio_file.read()
            audio_stream = BytesIO(audio_bytes)
            audio_stream.seek(0)
                
            transcript = client.audio.transcriptions.create(
                     model="whisper-1",
                    file=(audio_file.filename, audio_stream, audio_file.mimetype),
                    language=language  # Optional language hint
                )
            
            return jsonify({
                'text': transcript.text,
                'language': language
            }), 200
            
        except Exception as whisper_error:
            logging.error(f"Whisper transcription error: {whisper_error}")
            return jsonify({'error': 'Failed to transcribe audio'}), 500
            
    except Exception as e:
        logging.error(f"Transcribe endpoint error: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@chat_bp.route('/debug-prompt', methods=['GET'])
@token_required
def debug_prompt(user_id):
    """Debug endpoint to see what prompt would be generated"""
    try:
        from ..utils.file_utils import find_user_by_id
        from ..services.prompt_builder import PromptBuilder
        
        # Get user data
        user_data = find_user_by_id(user_id)
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        # Get minimal conversation context
        conversation_context = {
            'recent_messages': [],
            'conversation_summaries': [],
            'message_count': 0
        }
        
        # Build prompt
        prompt_builder = PromptBuilder()
        system_prompt, detected_level = prompt_builder.build_prompt(
            user_data,
            conversation_context,
            "Test message",
            mode='chat'
        )
        
        return jsonify({
            'user_level': detected_level,
            'prompt_preview': system_prompt[:500] + '...' if len(system_prompt) > 500 else system_prompt,
            'full_prompt': system_prompt,
            'prompt_length': len(system_prompt)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500