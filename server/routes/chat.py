from flask import Blueprint, request, jsonify
from utils.auth_utils import token_required
from services.chat_service import ChatService

chat_bp = Blueprint('chat', __name__)

def get_chat_service():
    """Factory function to get chat service instance"""
    return ChatService()

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
        
        # Get chat service instance
        chat_service = get_chat_service()
        
        # Generate response
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
            'audio_language': result['audio_language'],
            'conversation_id': result['conversation_id']
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@chat_bp.route('/history', methods=['GET'])
@token_required
def get_history(user_id):
    """Get conversation history for current session"""
    try:
        chat_service = get_chat_service()
        history = chat_service.get_conversation_history(user_id)
        return jsonify(history), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@chat_bp.route('/new-session', methods=['POST'])
@token_required
def new_session(user_id):
    """Start a new conversation session"""
    try:
        chat_service = get_chat_service()
        # Clear current conversation
        if hasattr(chat_service, 'conversations') and user_id in chat_service.conversations:
            del chat_service.conversations[user_id]
        
        return jsonify({'message': 'New session started'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500