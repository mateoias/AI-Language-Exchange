# routes/chat.py
import logging
from io import BytesIO
import traceback
from datetime import datetime, time
from flask import Blueprint, request, jsonify, current_app
from ..utils.auth_utils import token_required
from ..services.chat_service import ChatService
from ..services.audio_service import AudioService
from ..services.simplified_chat_service import SimplifiedChatService
from ..services.debug_chat_service import DebugChatService

chat_bp = Blueprint('chat', __name__)

# Service instances - will be initialized when first used
_chat_service = None
_audio_service = None
_simplified_chat_service = None
USE_SIMPLIFIED_SERVICE = False

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

def get_simplified_chat_service():
    """Get or create simplified chat service instance"""
    global _simplified_chat_service
    if _simplified_chat_service is None:
        speech_key = current_app.config.get('AZURE_SPEECH_KEY')
        speech_region = current_app.config.get('AZURE_SPEECH_REGION')
        _simplified_chat_service = SimplifiedChatService(speech_key, speech_region)
    return _simplified_chat_service


@chat_bp.route('/message', methods=['POST'])
@token_required
def send_message(user_id):
    """
    Main message endpoint - can use either service based on flag
    """
    try:
        # Check which service to use
        if USE_SIMPLIFIED_SERVICE:
            print("🔄 Using simplified service for /message endpoint")
            # Call the simplified logic directly, not the function
            return handle_simplified_message(user_id)
        else:
            print("🔄 Using original service for /message endpoint")
            return handle_original_message(user_id)
            
    except Exception as e:
        print("💥 Exception in main message endpoint:", e)
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


def handle_simplified_message(user_id):
    """
    Handle message using simplified service (extracted from send_message_simplified)
    """
    try:
        data = request.get_json()
        print("📩 Simplified service - Incoming data:", data)
        
        if not data or not data.get('message'):
            return jsonify({'error': 'Message content is required'}), 400
        
        message_content = data['message'].strip()
        if not message_content:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        audio_speed = data.get('audio_speed', 0.8)
        if not 0.5 <= audio_speed <= 1.5:
            audio_speed = 0.8

        print("🚀 Calling simplified_chat_service.generate_response...")
        start_time = datetime.now()
        
        result = get_simplified_chat_service().generate_response(user_id, message_content, audio_speed)
        
        total_time = (datetime.now() - start_time).total_seconds() * 1000
        print(f"✅ Simplified service completed in {total_time:.0f}ms")

        if result.get('error'):
            print(f"❌ Simplified service error: {result['error']}")
            return jsonify(result), 500

        # Add performance metrics to response
        result['performance'] = result.get('performance', {})
        result['performance']['endpoint'] = 'simplified'
        result['performance']['total_endpoint_time_ms'] = total_time

        # Generate user audio (same as original)
        user_audio_data = None
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
            print(f"⚠️  User audio generation failed: {e}")

        # Return the response in the format expected by your frontend
        response_data = {
            'segments': result['segments'],
            'intent': result.get('intent', 'chat'),
            'audio_language': result.get('audio_language', 'en'),
            'user_audio_data': user_audio_data,
            'rephrased': len([s for s in result['segments'] if s['type'] == 'rephrase']) > 0,
            'performance': result.get('performance', {})
        }

        print(f"📤 Returning {len(result['segments'])} segments")
        return jsonify(response_data), 200

    except Exception as e:
        print("💥 Exception in simplified message handler:", e)
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


def handle_original_message(user_id):
    """
    Handle message using original service (your existing logic)
    """
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

        print("Calling original chat_service.generate_response...")
        result = get_chat_service().generate_response(user_id, message_content, audio_speed)

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

        # Return the full segments structure
        if 'segments' in result:
            # Get user data for audio generation
            from ..utils.file_utils import find_user_by_id
            user_data = find_user_by_id(user_id)
            
            # Generate user audio (optional)
            user_audio_data = None
            try:
                if user_data:
                    user_audio_data = get_audio_service().generate_audio(
                        message_content,
                        user_data['learningLanguage'],
                        audio_speed
                    )
            except Exception as e:
                print(f"User audio generation failed: {e}")

            # Return the full segments response
            return jsonify({
                'segments': result['segments'],
                'intent': result.get('intent', 'unknown'),
                'audio_language': result.get('audio_language', 'en'),
                'user_audio_data': user_audio_data,
                'rephrased': result.get('rephrased', False)
            }), 200
        
        else:
            # Fallback for old format
            return jsonify({
                'response': result.get('response', ''),
                'intent': result.get('intent', 'unknown'),
                'audio_language': result.get('audio_language', 'en'),
                'audio_data': result.get('audio_data'),
                'user_audio_data': None
            }), 200

    except Exception as e:
        print("Exception in original message handler:", e)
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
    
@chat_bp.route('/message-simplified', methods=['POST'])
@token_required
def send_message_simplified(user_id):
    """
    NEW: Simplified message endpoint using single LLM call
    Use this to test the new architecture vs the old one
    """
    try:
        data = request.get_json()
        print("📩 Simplified endpoint - Incoming data:", data)
        
        if not data or not data.get('message'):
            return jsonify({'error': 'Message content is required'}), 400
        
        message_content = data['message'].strip()
        if not message_content:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        audio_speed = data.get('audio_speed', 0.8)
        if not 0.5 <= audio_speed <= 1.5:
            audio_speed = 0.8

        print("🚀 Calling simplified_chat_service.generate_response...")
        start_time = datetime.now()
        
        result = get_simplified_chat_service().generate_response(user_id, message_content, audio_speed)
        
        total_time = (datetime.now() - start_time).total_seconds() * 1000
        print(f"✅ Simplified service completed in {total_time:.0f}ms")

        if result.get('error'):
            print(f"❌ Simplified service error: {result['error']}")
            return jsonify(result), 500

        # Add performance metrics to response
        result['performance'] = result.get('performance', {})
        result['performance']['endpoint'] = 'simplified'
        result['performance']['total_endpoint_time_ms'] = total_time

        # Generate user audio (same as original)
        user_audio_data = None
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
            print(f"⚠️  User audio generation failed: {e}")

        # Return the response
        response_data = {
            'segments': result['segments'],
            'intent': result.get('intent', 'chat'),
            'audio_language': result.get('audio_language', 'en'),
            'user_audio_data': user_audio_data,
            'rephrased': len([s for s in result['segments'] if s['type'] == 'rephrase']) > 0,
            'performance': result.get('performance', {})
        }

        print(f"📤 Returning {len(result['segments'])} segments")
        return jsonify(response_data), 200

    except Exception as e:
        print("💥 Exception in simplified endpoint:", e)
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@chat_bp.route('/compare-approaches', methods=['POST'])
@token_required  
def compare_approaches(user_id):
    """
    Compare old vs new approach side by side
    Returns timing data for both approaches
    """
    try:
        data = request.get_json()
        message_content = data['message'].strip()
        audio_speed = data.get('audio_speed', 0.8)
        
        print(f"🔬 COMPARISON TEST for message: '{message_content}'")
        
        # Test original approach
        print("\n📊 Testing ORIGINAL approach...")
        original_start = datetime.now()
        
        try:
            original_result = get_chat_service().generate_response(user_id, message_content, audio_speed)
            original_time = (datetime.now() - original_start).total_seconds() * 1000
            original_success = True
        except Exception as e:
            original_time = (datetime.now() - original_start).total_seconds() * 1000
            original_result = {'error': str(e)}
            original_success = False
        
        # Test simplified approach  
        print("\n📊 Testing SIMPLIFIED approach...")
        simplified_start = datetime.now()
        
        try:
            simplified_result = get_simplified_chat_service().generate_response(user_id, message_content, audio_speed)
            simplified_time = (datetime.now() - simplified_start).total_seconds() * 1000
            simplified_success = True
        except Exception as e:
            simplified_time = (datetime.now() - simplified_start).total_seconds() * 1000
            simplified_result = {'error': str(e)}
            simplified_success = False
        
        # Calculate improvement
        if original_success and simplified_success:
            improvement_percent = ((original_time - simplified_time) / original_time) * 100
        else:
            improvement_percent = None
        
        comparison_results = {
            'message': message_content,
            'original': {
                'success': original_success,
                'time_ms': original_time,
                'segments_count': len(original_result.get('segments', [])) if original_success else 0,
                'result': original_result if original_success else {'error': original_result.get('error')}
            },
            'simplified': {
                'success': simplified_success,
                'time_ms': simplified_time,
                'segments_count': len(simplified_result.get('segments', [])) if simplified_success else 0,
                'result': simplified_result if simplified_success else {'error': simplified_result.get('error')}
            },
            'improvement': {
                'time_saved_ms': original_time - simplified_time if original_success and simplified_success else None,
                'percent_faster': improvement_percent,
                'summary': f"Simplified approach was {improvement_percent:.1f}% faster" if improvement_percent else "Unable to calculate improvement"
            }
        }
        
        print(f"\n📈 COMPARISON RESULTS:")
        print(f"   Original: {original_time:.0f}ms ({'✅' if original_success else '❌'})")
        print(f"   Simplified: {simplified_time:.0f}ms ({'✅' if simplified_success else '❌'})")
        if improvement_percent:
            print(f"   Improvement: {improvement_percent:.1f}% faster")
        
        return jsonify(comparison_results), 200
        
    except Exception as e:
        return jsonify({'error': f'Comparison failed: {str(e)}'}), 500

@chat_bp.route('/switch-to-simplified', methods=['POST'])
@token_required
def switch_to_simplified(user_id):
    """
    Switch the main /message endpoint to use simplified approach
    This modifies the routing behavior
    """
    try:
        # This is a simple toggle - in production you'd want this to be 
        # controlled by environment variables or database settings
        global USE_SIMPLIFIED_SERVICE
        USE_SIMPLIFIED_SERVICE = True
        
        return jsonify({
            'message': 'Switched to simplified service',
            'note': 'The /message endpoint will now use the single LLM call approach'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Switch failed: {str(e)}'}), 500

# Add these new routes to server/routes/chat.py

@chat_bp.route('/message-optimized', methods=['POST'])
@token_required
def send_message_optimized(user_id):
    """
    OPTIMIZED simplified endpoint with concise prompts and optional audio
    """
    try:
        data = request.get_json()
        message_content = data['message'].strip()
        audio_speed = data.get('audio_speed', 0.8)
        skip_audio = data.get('skip_audio', False)  # New parameter
        
        print(f"📩 Optimized endpoint - Message: '{message_content}' | Skip audio: {skip_audio}")
        
        start_time = datetime.now()
        
        result = get_simplified_chat_service().generate_response(
            user_id, 
            message_content, 
            audio_speed, 
            skip_audio=skip_audio  # Pass the skip_audio parameter
        )
        
        total_time = (datetime.now() - start_time).total_seconds() * 1000
        print(f"✅ Optimized service completed in {total_time:.0f}ms")

        if result.get('error'):
            return jsonify(result), 500

        # Add endpoint performance metrics
        result['performance'] = result.get('performance', {})
        result['performance']['endpoint'] = 'optimized'
        result['performance']['total_endpoint_time_ms'] = total_time

        # Generate user audio (same as original)
        user_audio_data = None
        if not skip_audio:
            try:
                user_data = find_user_by_id(user_id)
                if user_data:
                    user_audio_data = get_audio_service().generate_audio(
                        message_content,
                        user_data['learningLanguage'],
                        audio_speed
                    )
            except Exception as e:
                print(f"⚠️  User audio generation failed: {e}")

        response_data = {
            'segments': result['segments'],
            'intent': result.get('intent', 'chat'),
            'audio_language': result.get('audio_language', 'en'),
            'user_audio_data': user_audio_data,
            'rephrased': len([s for s in result['segments'] if s['type'] == 'rephrase']) > 0,
            'performance': result.get('performance', {})
        }

        return jsonify(response_data), 200

    except Exception as e:
        print("💥 Exception in optimized endpoint:", e)
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@chat_bp.route('/test-llm-only', methods=['POST'])
@token_required  
def test_llm_only(user_id):
    """
    Test ONLY the LLM performance without any audio generation
    """
    try:
        data = request.get_json()
        message_content = data['message'].strip()
        
        print(f"🧪 LLM-ONLY TEST - Message: '{message_content}'")
        
        # Test original LLM performance (estimate)
        print("\n📊 Testing ORIGINAL LLM approach...")
        original_start = datetime.now()
        
        # Simulate original: Intent + Rephrase + Response (3 LLM calls)
        # We'll make 3 separate simple calls to estimate
        try:
            # Simulate intent detection (fast)
            llm_manager.generate_chat_response(
                messages=[{"role": "user", "content": f"Classify this message intent: {message_content}"}],
                max_tokens=20,
                log_request=False
            )
            
            # Simulate rephrase call
            llm_manager.generate_chat_response(
                messages=[{"role": "user", "content": f"Rephrase this into a complete sentence: {message_content}"}],
                max_tokens=50,
                log_request=False
            )
            
            # Simulate main response
            llm_manager.generate_chat_response(
                messages=[{"role": "user", "content": f"Respond to student in Spanish: {message_content}"}],
                max_tokens=100,
                log_request=False
            )
            
            original_llm_time = (datetime.now() - original_start).total_seconds() * 1000
            original_success = True
        except Exception as e:
            original_llm_time = (datetime.now() - original_start).total_seconds() * 1000
            original_success = False
            print(f"   ❌ Original simulation failed: {e}")
        
        # Test optimized approach (no audio)
        print("\n📊 Testing OPTIMIZED LLM approach...")
        optimized_start = datetime.now()
        
        try:
            result = get_simplified_chat_service().generate_response(
                user_id, 
                message_content, 
                audio_speed=0.8, 
                skip_audio=True  # No audio
            )
            optimized_llm_time = result.get('performance', {}).get('llm_time_ms', 0)
            optimized_success = True
        except Exception as e:
            optimized_llm_time = (datetime.now() - optimized_start).total_seconds() * 1000
            optimized_success = False
            print(f"   ❌ Optimized approach failed: {e}")
        
        # Calculate improvement
        if original_success and optimized_success and original_llm_time > 0:
            improvement_percent = ((original_llm_time - optimized_llm_time) / original_llm_time) * 100
        else:
            improvement_percent = None
        
        results = {
            'message': message_content,
            'llm_only_comparison': {
                'original_estimated': {
                    'success': original_success,
                    'llm_time_ms': original_llm_time,
                    'description': '3 separate LLM calls (intent + rephrase + response)'
                },
                'optimized': {
                    'success': optimized_success,
                    'llm_time_ms': optimized_llm_time,
                    'description': '1 structured LLM call',
                    'prompt_length': result.get('performance', {}).get('prompt_length', 0) if optimized_success else 0
                },
                'improvement': {
                    'time_saved_ms': original_llm_time - optimized_llm_time if original_success and optimized_success else None,
                    'percent_faster': improvement_percent,
                    'summary': f"Optimized LLM is {improvement_percent:.1f}% faster" if improvement_percent and improvement_percent > 0 else f"Optimized LLM is {abs(improvement_percent):.1f}% slower" if improvement_percent else "Unable to calculate"
                }
            }
        }
        
        print(f"\n📈 LLM-ONLY RESULTS:")
        print(f"   Original (3 calls): {original_llm_time:.0f}ms")
        print(f"   Optimized (1 call): {optimized_llm_time:.0f}ms")
        if improvement_percent:
            if improvement_percent > 0:
                print(f"   🚀 LLM improvement: {improvement_percent:.1f}% faster")
            else:
                print(f"   🐌 LLM regression: {abs(improvement_percent):.1f}% slower")
        
        return jsonify(results), 200
        
    except Exception as e:
        return jsonify({'error': f'LLM test failed: {str(e)}'}), 500


@chat_bp.route('/quick-comparison', methods=['POST'])
@token_required
def quick_comparison(user_id):
    """
    Quick comparison with optimized settings
    """
    try:
        data = request.get_json()
        message_content = data['message'].strip()
        
        print(f"⚡ QUICK COMPARISON for: '{message_content}'")
        
        # Test original (with audio)
        print("\n📊 Original (with audio)...")
        orig_start = datetime.now()
        try:
            orig_result = get_chat_service().generate_response(user_id, message_content, 0.8)
            orig_time = (datetime.now() - orig_start).total_seconds() * 1000
            orig_success = True
        except Exception as e:
            orig_time = (datetime.now() - orig_start).total_seconds() * 1000
            orig_result = {'error': str(e)}
            orig_success = False
        
        # Test optimized (no audio)
        print("\n📊 Optimized (no audio)...")
        opt_start = datetime.now()
        try:
            opt_result = get_simplified_chat_service().generate_response(
                user_id, message_content, 0.8, skip_audio=True
            )
            opt_time = (datetime.now() - opt_start).total_seconds() * 1000
            opt_success = True
        except Exception as e:
            opt_time = (datetime.now() - opt_start).total_seconds() * 1000
            opt_result = {'error': str(e)}
            opt_success = False
        
        # Calculate improvement
        improvement = None
        if orig_success and opt_success:
            improvement = ((orig_time - opt_time) / orig_time) * 100
        
        comparison = {
            'message': message_content,
            'original': {
                'success': orig_success,
                'total_time_ms': orig_time,
                'segments': len(orig_result.get('segments', [])) if orig_success else 0
            },
            'optimized_no_audio': {
                'success': opt_success,
                'total_time_ms': opt_time,
                'llm_time_ms': opt_result.get('performance', {}).get('llm_time_ms', 0) if opt_success else 0,
                'segments': len(opt_result.get('segments', [])) if opt_success else 0,
                'prompt_length': opt_result.get('performance', {}).get('prompt_length', 0) if opt_success else 0
            },
            'improvement_percent': improvement
        }
        
        print(f"\n⚡ QUICK RESULTS:")
        print(f"   Original: {orig_time:.0f}ms | Optimized: {opt_time:.0f}ms")
        if improvement:
            print(f"   Improvement: {improvement:.1f}% {'faster' if improvement > 0 else 'slower'}")
        
        return jsonify(comparison), 200
        
    except Exception as e:
        return jsonify({'error': f'Quick comparison failed: {str(e)}'}), 500
    
# Add this import to the top of chat.py

# Add this route to chat.py
@chat_bp.route('/debug-prompts', methods=['POST'])
@token_required
def debug_prompts(user_id):
    """
    DEBUG: Analyze what's making prompts slow
    """
    try:
        data = request.get_json()
        message = data.get('message', 'yes')
        
        print(f"🔍 DEBUGGING PROMPTS for user {user_id}, message: '{message}'")
        
        debug_service = DebugChatService()
        
        # Analyze prompt content
        analysis = debug_service.analyze_prompt_content(user_id, message)
        
        if analysis:
            # Also test token limits
            print(f"\n" + "="*60)
            debug_service.test_token_limits(user_id, message)
            
            return jsonify({
                'analysis': analysis,
                'recommendations': [
                    f"Minimal prompt: {analysis['minimal_prompt_time']:.0f}ms",
                    f"Complex prompt: {analysis['complex_prompt_time']:.0f}ms", 
                    f"Speedup factor: {analysis['complex_prompt_time'] / analysis['minimal_prompt_time']:.1f}x slower with context",
                    f"Context messages: {analysis['context_messages']}"
                ]
            }), 200
        else:
            return jsonify({'error': 'Debug analysis failed'}), 500
            
    except Exception as e:
        print(f"❌ Debug route error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Debug failed: {str(e)}'}), 500


@chat_bp.route('/test-minimal', methods=['POST'])
@token_required
def test_minimal(user_id):
    """
    Test the absolute minimal prompt approach
    """
    try:
        data = request.get_json()
        message = data.get('message', 'yes')
        
        print(f"🧪 TESTING MINIMAL APPROACH: '{message}'")
        
        user_data = find_user_by_id(user_id)
        level = user_data.get('proficiencyLevel', 'beginner')
        learning_lang = user_data['learningLanguage']
        
        # Ultra-minimal prompt
        if level == 'beginner':
            prompt = f"Help student practice {learning_lang}. If 1-2 words, rephrase to complete sentence. JSON: {{\"rephrase\": \"...\", \"response\": \"{learning_lang} reply\", \"include_rephrase\": true/false}}"
        else:
            prompt = f"Help student practice {learning_lang}. Rarely rephrase. JSON: {{\"rephrase\": \"...\", \"response\": \"{learning_lang} reply\", \"include_rephrase\": true/false}}"
        
        print(f"   Prompt length: {len(prompt)} chars")
        print(f"   Prompt: {prompt}")
        
        start_time = datetime.now()
        
        response = llm_manager.generate_chat_response(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": message}
            ],
            temperature=0.7,
            max_tokens=80,  # Very low token limit
            log_request=True
        )
        
        duration = (datetime.now() - start_time).total_seconds() * 1000
        
        print(f"   ⚡ Minimal response time: {duration:.0f}ms")
        print(f"   Response: {response}")
        
        # Try to parse JSON
        try:
            parsed = json.loads(response)
            segments = []
            
            if parsed.get('include_rephrase') and parsed.get('rephrase'):
                segments.append({
                    'type': 'rephrase',
                    'text': parsed['rephrase'],
                    'persona': 'teacher'
                })
            
            if parsed.get('response'):
                segments.append({
                    'type': 'response', 
                    'text': parsed['response'],
                    'persona': 'partner'
                })
            
            return jsonify({
                'success': True,
                'duration_ms': duration,
                'prompt_length': len(prompt),
                'segments': segments,
                'raw_response': response,
                'approach': 'ultra_minimal'
            }), 200
            
        except json.JSONDecodeError:
            return jsonify({
                'success': False,
                'duration_ms': duration,
                'prompt_length': len(prompt),
                'raw_response': response,
                'error': 'JSON parsing failed',
                'approach': 'ultra_minimal'
            }), 200
            
    except Exception as e:
        print(f"❌ Minimal test error: {e}")
        return jsonify({'error': f'Minimal test failed: {str(e)}'}), 500
    

# Add this test endpoint to server/routes/chat.py

@chat_bp.route('/test-parallel', methods=['GET'])
@token_required
def test_parallel(user_id):
    """Test endpoint to verify parallel processing is working"""
    try:
        # Test with a simple message
        test_message = "sí"
        
        # Get timings for both sequential and parallel
        from flask import current_app
        
        # Test sequential
        current_app.config['USE_PARALLEL_PROCESSING'] = False
        start_seq = time.time()
        seq_result = get_chat_service().generate_response(user_id, test_message, 0.8)
        seq_time = time.time() - start_seq
        
        # Test parallel
        current_app.config['USE_PARALLEL_PROCESSING'] = True
        start_par = time.time()
        par_result = get_chat_service().generate_response(user_id, test_message, 0.8)
        par_time = time.time() - start_par
        
        return jsonify({
            'sequential_time': seq_time,
            'parallel_time': par_time,
            'improvement': f"{((seq_time - par_time) / seq_time * 100):.1f}%",
            'parallel_generation_times': par_result.get('generation_times', {}),
            'segments_count': len(par_result.get('segments', []))
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500