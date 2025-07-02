from flask import Blueprint, request, jsonify
from ..models.user import User
from ..utils.auth_utils import hash_password, verify_password, generate_token, token_required
from ..utils.file_utils import load_users, save_users, find_user_by_email, find_user_by_id
import logging
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'nativeLanguage', 'learningLanguage']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} is required'}), 400
        
        # Check if user already exists
        existing_user_id, existing_user = find_user_by_email(data['email'])
        if existing_user:
            return jsonify({'message': 'User with this email already exists'}), 400
        
        # Create new user with proficiency level
        password_hash = hash_password(data['password'])
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=password_hash,
            native_language=data['nativeLanguage'],
            learning_language=data['learningLanguage'],
            proficiency_level=data.get('proficiencyLevel', 'beginner')  # Default to beginner
        )
        
        # Save user to file
        users_data = load_users()
        users_data[user.id] = user.to_dict()
        
        if save_users(users_data):
            # Generate token
            token = generate_token(user.id)
            
            return jsonify({
                'message': 'User created successfully',
                'token': token,
                'user': user.to_public_dict()
            }), 201
        else:
            return jsonify({'message': 'Failed to create user'}), 500
            
    except Exception as e:
        return jsonify({'message': f'Server error: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Email and password are required'}), 400
        
        # Find user
        user_id, user_data = find_user_by_email(data['email'])
        if not user_data:
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Verify password
        if not verify_password(data['password'], user_data['password_hash']):
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Update language preferences if provided
        if data.get('nativeLanguage') and data.get('learningLanguage'):
            user_data['nativeLanguage'] = data['nativeLanguage']
            user_data['learningLanguage'] = data['learningLanguage']
            
        # Update proficiency level if provided
        if data.get('proficiencyLevel'):
            user_data['proficiencyLevel'] = data['proficiencyLevel']
            
        # Save updates if any changes were made
        if data.get('nativeLanguage') or data.get('proficiencyLevel'):
            users_data = load_users()
            users_data[user_id] = user_data
            save_users(users_data)
        from ..services.conversation_service import ConversationService
        conv_service = ConversationService()
        conv_service.start_new_session(user_id)
        # Generate token
        token = generate_token(user_id)
        
        # Create user object for response
        user = User.from_dict(user_data)
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': user.to_public_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Server error: {str(e)}'}), 500

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(user_id):
    try:
        user_data = find_user_by_id(user_id)
        if not user_data:
            return jsonify({'message': 'User not found'}), 404
        
        user = User.from_dict(user_data)
        return jsonify(user.to_public_dict()), 200
        
    except Exception as e:
        return jsonify({'message': f'Server error: {str(e)}'}), 500

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(user_id):
    """Logout user and finalize current conversation"""
    try:
        # Import here to avoid circular imports
        from ..services.conversation_service import ConversationService
        conv_service = ConversationService()
        
        # Finalize and save current conversation before logout
        finalized_data = conv_service.finalize_conversation(user_id)
        conv_service.clear_session_without_save(user_id)

        return jsonify({
            'success': True,
            'message': 'Logged out successfully',
            'conversation_saved': bool(finalized_data),
            'message_count': finalized_data.get('message_count', 0) if finalized_data else 0
        }), 200
        
    except Exception as e:
        logging.error(f"Logout error: {e}")
        # Even if there's an error, allow logout
        return jsonify({
            'success': True,
            'message': 'Logged out with errors',
            'error': str(e)
        }), 200