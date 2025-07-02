# server/routes/chat.py (fixed version)
import logging
import time
from flask import Blueprint, request, jsonify, current_app
from ..utils.auth_utils import token_required
from ..services.chat_service import ChatService
from ..services.audio_service import AudioService
from ..services.conversation_service import ConversationService

chat_bp = Blueprint('chat', __name__)

# Service instances
_chat_service = None
_audio_service = None

def get_chat_service():
    """Get or create chat service instance"""
    global _chat_service
    if _chat_service is None:
        speech_key = current_app.config.get('AZURE_SPEECH_KEY')
        speech_region = current_app.config.get('AZURE_SPEECH_REGION')
        _chat_service = ChatService(speech_key, speech_region)
    return _chat_service

def get_audio_service():
    """Get or create audio service instance"""
    global _audio_service
    if _audio_service is None:
        speech_key = current_app.config.get('AZURE_SPEECH_KEY')
        speech_region = current_app.config.get('AZURE_SPEECH_REGION')
        _audio_service = AudioService(speech_key, speech_region)
    return _audio_service

@chat_bp.route('/message', methods=['POST'])
@token_required
def send_message(user_id):
    """
    Main message endpoint - now unified and simplified
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('message'):
            return jsonify({'error': 'Message content is required'}), 400
        
        message_content = data['message'].strip()
        if not message_content:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        audio_speed = data.get('audio_speed', 0.8)
        if not 0.5 <= audio_speed <= 1.5:
            audio_speed = 0.8
        
        # Use unified service for everything
        start_time = time.time()
        result = get_chat_service().generate_response(
            user_id, 
            message_content, 
            audio_speed
        )
        total_time = (time.time() - start_time) * 1000
        
        # Add performance metrics
        result['performance'] = result.get('performance', {})
        result['performance']['total_endpoint_time_ms'] = total_time
        
        # Generate user audio if requested
        user_audio_data = None
        if data.get('generate_user_audio', True):
            try:
                from ..utils.file_utils import find_user_by_id
                user_data = find_user_by_id(user_id)
                if user_data:
                    user_audio_data = get_audio_service().generate_audio(
                        message_content,
                        user_data['learningLanguage'],
                        audio_speed
                    )
            except Exception as e:
                logging.warning(f"User audio generation failed: {e}")
        
        # Build response
        response_data = {
            'segments': result['segments'],
            'intent': result.get('intent', 'chat'),
            'audio_language': result.get('audio_language', 'en'),
            'user_audio_data': user_audio_data,
            'performance': result.get('performance', {})
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logging.error(f"Message endpoint error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@chat_bp.route('/history', methods=['GET'])
@token_required
def get_history(user_id):
    """Get conversation history"""
    try:
        conv_service = ConversationService()
        history = conv_service.get_conversation_history(user_id)
        return jsonify(history), 200
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@chat_bp.route('/new-session', methods=['POST'])
@token_required
def new_session(user_id):
    """Start a new conversation session"""
    try:
        conv_service = ConversationService()
        
        # Get request data - handle both cases (with or without body)
        try:
            data = request.get_json() or {}
        except:
            data = {}
        
        save_current = data.get('save_current', False)
        
        if save_current:
            # Finalize and save current conversation
            conv_service.finalize_conversation(user_id)
        else:
            # Just clear without saving
            conv_service.clear_session_without_save(user_id)
        
        # Clear audio cache
        get_audio_service().clear_cache()
        
        return jsonify({
            "message": "New session started",
            "success": True,
            "saved_previous": save_current
        }), 200
        
    except Exception as e:
        logging.error(f"New session error: {e}")
        import traceback
        traceback.print_exc()
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
        
        if not 0.5 <= audio_speed <= 1.5:
            audio_speed = 0.8
        
        audio_data = get_audio_service().generate_audio(text, language, audio_speed)
        
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
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No audio file selected'}), 400
        
        language = request.form.get('language', None)
        
        try:
            from openai import OpenAI
            from io import BytesIO
            
            client = OpenAI(api_key=current_app.config.get('OPENAI_API_KEY'))
            
            audio_bytes = audio_file.read()
            audio_stream = BytesIO(audio_bytes)
            audio_stream.seek(0)
            
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=(audio_file.filename, audio_stream, audio_file.mimetype),
                language=language
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

@chat_bp.route('/finalize-conversation', methods=['POST'])
@token_required
def finalize_conversation(user_id):
    """Finalize current conversation for database storage"""
    try:
        conv_service = ConversationService()
        finalized_data = conv_service.finalize_conversation(user_id)
        
        if finalized_data:
            return jsonify({
                'success': True,
                'conversation_id': finalized_data['conversation_id'],
                'message_count': finalized_data['message_count'],
                'summary': finalized_data.get('final_summary', '')
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'No active conversation to finalize'
            }), 200
            
    except Exception as e:
        logging.error(f"Finalize conversation error: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500