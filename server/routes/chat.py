from flask import Blueprint, request, jsonify
from utils.auth_utils import token_required
from services.chat_service import ChatService

chat_bp = Blueprint('chat', __name__)

# CHANGED: Create single service instance instead of factory function
chat_service = ChatService()

@chat_bp.route('/message', methods=['POST'])
@token_required
def send_message(user_id):
    """Send a message and get bot response"""
    try:
        data = request.get_json()
        
        if not data or not data.get('message'):
            return jsonify({'error': 'Message content is required'}), 400
        
        message_content = data['message'].strip()
        if not message_content:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Generate response using persistent service
        result = chat_service.generate_response(user_id, message_content)
        
        if 'error' in result:
            return jsonify({
                'response': result['response'],
                'intent': result['intent'],
                'audio_language': result['audio_language']
            }), 500
        
        return jsonify({
            'response': result['response'],
            'intent': result['intent'],
            'audio_language': result['audio_language']
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