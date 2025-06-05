from flask import Blueprint, request, jsonify
from utils.auth_utils import token_required
from utils.file_utils import find_user_by_id, update_user
from models.user import User

user_bp = Blueprint('user', __name__)

@user_bp.route('/personalization', methods=['PUT'])
@token_required
def update_personalization(user_id):
    try:
        data = request.get_json()
        
        # Get current user data
        user_data = find_user_by_id(user_id)
        if not user_data:
            return jsonify({'message': 'User not found'}), 404
        
        # Update personalization data
        user_data['personalization'] = data
        
        if update_user(user_id, user_data):
            user = User.from_dict(user_data)
            return jsonify({
                'message': 'Personalization updated successfully',
                'user': user.to_public_dict()
            }), 200
        else:
            return jsonify({'message': 'Failed to update personalization'}), 500
            
    except Exception as e:
        return jsonify({'message': f'Server error: {str(e)}'}), 500

@user_bp.route('/personalization', methods=['DELETE'])
@token_required
def delete_personalization(user_id):
    try:
        # Get current user data
        user_data = find_user_by_id(user_id)
        if not user_data:
            return jsonify({'message': 'User not found'}), 404
        
        # Clear personalization data
        user_data['personalization'] = {}
        
        if update_user(user_id, user_data):
            user = User.from_dict(user_data)
            return jsonify({
                'message': 'Personalization data deleted successfully',
                'user': user.to_public_dict()
            }), 200
        else:
            return jsonify({'message': 'Failed to delete personalization'}), 500
            
    except Exception as e:
        return jsonify({'message': f'Server error: {str(e)}'}), 500

@user_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(user_id):
    try:
        data = request.get_json()
        
        # Get current user data
        user_data = find_user_by_id(user_id)
        if not user_data:
            return jsonify({'message': 'User not found'}), 404
        
        # Update allowed fields
        allowed_fields = ['username', 'nativeLanguage', 'learningLanguage']
        for field in allowed_fields:
            if field in data:
                user_data[field] = data[field]
        
        if update_user(user_id, user_data):
            user = User.from_dict(user_data)
            return jsonify({
                'message': 'Profile updated successfully',
                'user': user.to_public_dict()
            }), 200
        else:
            return jsonify({'message': 'Failed to update profile'}), 500
            
    except Exception as e:
        return jsonify({'message': f'Server error: {str(e)}'}), 500