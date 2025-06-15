from flask import Blueprint, request, jsonify
from ..utils.auth_utils import token_required
from ..utils.file_utils import find_user_by_id, update_user
from ..models.user import User
import logging
from ..database import setup_user_graph, update_from_personalization, get_user_context
from ..services.personalization_service import PersonalizationService

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
        
        # Update personalization data in JSON file first
        user_data['personalization'] = data
        
        # Process personalization using the service
        try:
            personalization_service = PersonalizationService()
            # Pass the RAW form data (not processed data)
            extracted_data = personalization_service.process_personalization(user_id, data)
            
            # Log success or any issues with graph processing
            if extracted_data:
                logging.info(f"Personalization extracted and processed for user {user_id}")
                logging.info(f"Extracted {len(extracted_data.get('entities', []))} entities and {len(extracted_data.get('relationships', []))} relationships")
            else:
                logging.warning(f"No data extracted for user {user_id}")
                
        except Exception as graph_error:
            # Log the graph processing error but don't fail the request
            logging.error(f"Graph processing failed for user {user_id}: {graph_error}")
            import traceback
            logging.error(f"Graph processing traceback: {traceback.format_exc()}")
            # Continue to save to JSON even if graph processing fails
        
        # Save to file system
        if update_user(user_id, user_data):
            user = User.from_dict(user_data)
            return jsonify({
                'message': 'Personalization updated successfully',
                'user': user.to_public_dict()
            }), 200
        else:
            return jsonify({'message': 'Failed to update personalization'}), 500
            
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
        
        # TODO: Also clear graph data if needed
        # You might want to add a method to PersonalizationService to handle deletion
        
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