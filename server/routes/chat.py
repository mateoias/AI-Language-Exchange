# routes/chat.py
import logging
from io import BytesIO
import traceback
from flask import Blueprint, request, jsonify, current_app
from ..utils.auth_utils import token_required
from ..services.chat_service import ChatService
from ..services.audio_service import AudioService

chat_bp = Blueprint('chat', __name__)

# Service instances - will be initialized when first used
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
    try:
        data = request.get_json()
        print("Incoming data:", data)
        
        if not data or not data.get('message'):
            return jsonify({'error': 'Message content is required'}), 400
        
        message_content = data['message'].strip()
        if not message_content:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        audio_speed = data.get('audio_speed', 0.8)
        if not 0.5 <= audio_speed <= 1.5:
            audio_speed = 0.8

        print("Calling chat_service.generate_response...")
        result = get_chat_service().generate_response(user_id, message_content, audio_speed)
# print("Chat result:", result)
        if result.get('error'):
            print(f"Chat error: {result['error']}")
        else:
            print(f"Chat response generated with {len(result.get('segments', []))} segments")

        # Check for error in response
        if 'error' in result:
            return jsonify({
                'response': '',
                'intent': result.get('intent', 'unknown'),
                'audio_language': result.get('audio_language', 'en'),
                'audio_data': result.get('audio_data')
            }), 500

        # NEW: Return the full segments structure
        if 'segments' in result:
            # Get user data for audio generation
            from ..utils.file_utils import find_user_by_id
            user_data = find_user_by_id(user_id)
            
            # Generate user audio (optional)
            user_audio_data = None
            try:
                print("Calling audio_service.generate_audio for user message...")
                if user_data:
                    user_audio_data = get_audio_service().generate_audio(
                        message_content,
                        user_data['learningLanguage'],  # Fixed: need language parameter
                        audio_speed
                    )
                    print("User audio generated")
            except Exception as e:
                print(f"User audio generation failed: {e}")
                traceback.print_exc()

            # Return the full segments response
            return jsonify({
                'segments': result['segments'],
                'intent': result.get('intent', 'unknown'),
                'audio_language': result.get('audio_language', 'en'),
                'user_audio_data': user_audio_data,
                'rephrased': result.get('rephrased', False)
            }), 200
        
        else:
            # Fallback for old format (shouldn't happen with new service)
            return jsonify({
                'response': result.get('response', ''),
                'intent': result.get('intent', 'unknown'),
                'audio_language': result.get('audio_language', 'en'),
                'audio_data': result.get('audio_data'),
                'user_audio_data': None
            }), 200

    except Exception as e:
        print("Exception in /message route:", e)
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@chat_bp.route('/message-legacy', methods=['POST'])
@token_required
def send_message_legacy(user_id):
    """Legacy endpoint for backward compatibility"""
    # This just wraps the response in the old format
    try:
        result = send_message(user_id)
        response_data = result[0].get_json()
        
        # Convert new format to old format
        if 'segments' in response_data:
            segments = response_data['segments']
            response_segment = next((s for s in segments if s['type'] == 'response'), None)
            
            legacy_response = {
                'response': response_segment['text'] if response_segment else '',
                'intent': response_data.get('intent', 'chat'),
                'audio_language': response_data.get('audio_language', ''),
                'audio_data': response_segment['audio_data'] if response_segment else None
            }
            
            return jsonify(legacy_response), 200
        
        return result
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@chat_bp.route('/history', methods=['GET'])
@token_required
def get_history(user_id):
    """Get conversation history for current session"""
    try:
        print(f"Received request for user_id: {user_id}")
        history = get_chat_service().get_conversation_history(user_id)
        print("History fetched:", history)
        return jsonify(history), 200
    except Exception as e:
        import traceback
        print("Error in get_history:", e)
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@chat_bp.route('/new-session', methods=['POST'])
@token_required
def new_session(user_id):
    """Start a new conversation session"""
    try:
        result = get_chat_service().start_new_session(user_id)
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@chat_bp.route('/finalize-conversation', methods=['POST'])
@token_required
def finalize_conversation(user_id):
    """Finalize current conversation for database storage"""
    try:
        finalized_data = get_chat_service().conversation_service.finalize_conversation(user_id)
        
        if finalized_data:
            return jsonify({
                'success': True,
                'conversation_id': finalized_data['conversation_id'],
                'message_count': finalized_data['message_count']
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'No active conversation to finalize'
            }), 200
            
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
        
        # Generate audio using the audio service - FIXED: use get_audio_service()
        audio_data = get_audio_service().generate_audio(text, language, audio_speed)
        
        if audio_data:
            return jsonify({'audio_data': audio_data}), 200
        else:
            return jsonify({'error': 'Failed to generate audio'}), 500
            
    except Exception as e:
        print(f"Error in regenerate_audio: {e}")
        import traceback
        traceback.print_exc()
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