from flask import Blueprint, request, jsonify
from ..utils.auth_utils import token_required
from ..utils.file_utils import find_user_by_id, update_user
from ..models.user import User
import logging
from ..database import setup_user_graph, update_from_personalization, get_user_context

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
        
        # Update personalization data (existing functionality)
        user_data['personalization'] = data
        
        # Save to file (existing functionality)
        file_update_success = update_user(user_id, user_data)
        if not file_update_success:
            return jsonify({'message': 'Failed to update personalization'}), 500
        
        # NEW: Process through LLM for graph updates
        graph_result = {"success": False, "updates": 0, "reasoning": "Not processed"}
        try:
            graph_result = update_from_personalization(
                user_id=user_data.get('id', user_id),  # Use user ID
                personalization_data=data
            )
            logging.info(f"Graph personalization result for user {user_id}: {graph_result}")
            
        except Exception as graph_error:
            # Don't fail the whole request if graph processing fails
            logging.error(f"Graph personalization update failed for user {user_id}: {graph_error}")
            graph_result = {"success": False, "error": str(graph_error), "updates": 0}
        
        # Return success with both file and graph info
        user = User.from_dict(user_data)
        return jsonify({
            'message': 'Personalization updated successfully',
            'user': user.to_public_dict(),
            'graph_updates': graph_result.get('updates', 0),
            'graph_reasoning': graph_result.get('reasoning', ''),
            'graph_success': graph_result.get('success', False)
        }), 200
            
    except Exception as e:
        logging.error(f"Personalization update error for user {user_id}: {e}")
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
        logging.error(f"Delete personalization error for user {user_id}: {e}")
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
        logging.error(f"Profile update error for user {user_id}: {e}")
        return jsonify({'message': f'Server error: {str(e)}'}), 500
    
@user_bp.route('/setup-graph', methods=['POST'])
@token_required
def setup_user_graph_endpoint(user_id):
    """Setup user in graph database"""
    try:
        user_data = find_user_by_id(user_id)
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        # Setup user node in graph
        graph_user_id = setup_user_graph(user_data)
        
        if graph_user_id:
            return jsonify({
                'message': 'User graph setup complete',
                'user_id': graph_user_id
            }), 200
        else:
            return jsonify({'error': 'Failed to setup user graph'}), 500
            
    except Exception as e:
        logging.error(f"User graph setup error for user {user_id}: {e}")
        return jsonify({'error': 'Graph setup failed'}), 500

@user_bp.route('/graph-context', methods=['GET'])
@token_required
def get_user_graph_context(user_id):
    """Get user's graph context for conversations"""
    try:
        user_data = find_user_by_id(user_id)
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        context = get_user_context(user_data.get('id', user_id))
        
        return jsonify(context), 200
        
    except Exception as e:
        logging.error(f"Get user context error for user {user_id}: {e}")
        return jsonify({'error': 'Failed to get user context'}), 500