from flask import Blueprint, request, jsonify
from utils.auth_utils import token_required
from services.chat_service import ChatService

chat_bp = Blueprint('chat', __name__)

# CHANGED: Create single service instance instead of factory function
chat_service = ChatService()

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
        
        # Generate audio only
        audio_data = chat_service.generate_audio(text, language, audio_speed)
        
        if audio_data:
            return jsonify({'audio_data': audio_data}), 200
        else:
            return jsonify({'error': 'Failed to generate audio'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500