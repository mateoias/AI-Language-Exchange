# server/services/debug_chat_service.py
"""
DEBUG version to see exactly what prompts are being generated
"""
import json
from typing import Dict, List, Optional
from .llm_manager import llm_manager
from .conversation_service import ConversationService
from ..utils.file_utils import find_user_by_id
from datetime import datetime

class DebugChatService:
    """
    Debug chat service to analyze prompt content and performance
    """
    
    def __init__(self):
        self.conversation_service = ConversationService()
    
    def analyze_prompt_content(self, user_id, message_content):
        """
        Analyze what's actually going into the prompt
        """
        print(f"\n🔍 DEBUG PROMPT ANALYSIS")
        print(f"=" * 60)
        
        try:
            # Get user data
            user_data = find_user_by_id(user_id)
            print(f"User: {user_data.get('username', 'Unknown')}")
            print(f"Level: {user_data.get('proficiencyLevel', 'Unknown')}")
            
            # Get conversation context
            conversation_context = self.conversation_service.get_conversation_context(user_id)
            
            print(f"\n📊 CONVERSATION CONTEXT:")
            print(f"Recent messages: {len(conversation_context.get('recent_messages', []))}")
            print(f"Chunk summaries: {len(conversation_context.get('chunk_summaries', []))}")
            print(f"Conversation summaries: {len(conversation_context.get('conversation_summaries', []))}")
            
            # Show recent messages
            recent_messages = conversation_context.get('recent_messages', [])
            if recent_messages:
                print(f"\n💬 RECENT MESSAGES ({len(recent_messages)}):")
                for i, msg in enumerate(recent_messages[-5:]):  # Show last 5
                    print(f"   {i+1}. {msg['sender']}: {msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}")
            
            # Test different prompt approaches
            print(f"\n🧪 TESTING DIFFERENT PROMPT APPROACHES:")
            
            # Approach 1: Minimal prompt (no context)
            minimal_prompt = self._build_minimal_prompt(user_data, message_content)
            print(f"\n1️⃣ MINIMAL PROMPT (no context):")
            print(f"   Length: {len(minimal_prompt)} chars")
            print(f"   Content: {minimal_prompt}")
            
            # Test minimal prompt performance
            print(f"\n   Testing minimal prompt...")
            start_time = datetime.now()
            minimal_response = llm_manager.generate_chat_response(
                messages=[
                    {"role": "system", "content": minimal_prompt},
                    {"role": "user", "content": message_content}
                ],
                temperature=0.7,
                max_tokens=100,
                log_request=False
            )
            minimal_time = (datetime.now() - start_time).total_seconds() * 1000
            print(f"   ⚡ Minimal time: {minimal_time:.0f}ms")
            print(f"   Response: {minimal_response}")
            
            # Approach 2: Current complex prompt
            current_prompt = self._build_current_complex_prompt(user_data, conversation_context, message_content)
            print(f"\n2️⃣ CURRENT COMPLEX PROMPT:")
            print(f"   Length: {len(current_prompt)} chars")
            print(f"   First 300 chars: {current_prompt[:300]}...")
            print(f"   Last 200 chars: ...{current_prompt[-200:]}")
            
            # Test current prompt performance
            print(f"\n   Testing complex prompt...")
            start_time = datetime.now()
            complex_response = llm_manager.generate_chat_response(
                messages=[
                    {"role": "system", "content": current_prompt},
                    {"role": "user", "content": message_content}
                ],
                temperature=0.7,
                max_tokens=100,
                log_request=False
            )
            complex_time = (datetime.now() - start_time).total_seconds() * 1000
            print(f"   ⚡ Complex time: {complex_time:.0f}ms")
            
            # Compare
            if minimal_time > 0 and complex_time > 0:
                factor = complex_time / minimal_time
                print(f"\n📊 COMPARISON:")
                print(f"   Minimal: {minimal_time:.0f}ms ({len(minimal_prompt)} chars)")
                print(f"   Complex: {complex_time:.0f}ms ({len(current_prompt)} chars)")
                print(f"   Complex is {factor:.1f}x slower")
                
                if factor > 2:
                    print(f"   🚨 Context is causing major slowdown!")
                elif factor > 1.5:
                    print(f"   ⚠️  Context is causing noticeable slowdown")
                else:
                    print(f"   ✅ Context impact is minimal")
            
            return {
                'minimal_prompt_time': minimal_time,
                'complex_prompt_time': complex_time,
                'minimal_prompt_length': len(minimal_prompt),
                'complex_prompt_length': len(current_prompt),
                'context_messages': len(recent_messages),
                'minimal_response': minimal_response,
                'complex_response': complex_response
            }
            
        except Exception as e:
            print(f"❌ Debug analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _build_minimal_prompt(self, user_data: Dict, message: str) -> str:
        """Build the absolute minimal prompt possible"""
        level = user_data.get('proficiencyLevel', 'beginner')
        learning_lang = user_data['learningLanguage']
        
        if level == 'beginner':
            rephrase_rule = "If they said 1-2 words, rephrase into complete sentence."
        else:
            rephrase_rule = "Rarely rephrase."
        
        return f"""Help student practice {learning_lang}. {rephrase_rule}

JSON format:
{{"rephrase": "complete sentence", "response": "reply in {learning_lang}", "include_rephrase": true/false}}

Student: "{message}" """
    
    def _build_current_complex_prompt(self, user_data: Dict, conversation_context: Dict, message: str) -> str:
        """Build the current complex prompt to see what's bloating it"""
        level = user_data.get('proficiencyLevel', 'beginner')
        learning_lang = user_data['learningLanguage']
        native_lang = user_data['nativeLanguage']
        
        # Get recent conversation for context
        recent_messages = conversation_context.get('recent_messages', [])[-3:]
        
        # Build conversation context (this might be the bloat!)
        if recent_messages:
            context_str = "Recent conversation:\n" + "\n".join([
                f"{msg['sender']}: {msg['content']}" for msg in recent_messages[-2:]
            ])
        else:
            context_str = "This is the start of your conversation."
        
        # Level-specific rules
        if level == 'beginner':
            rephrase_rule = "Rephrase short answers (1-3 words) into complete sentences."
            response_rule = "Use simple words, short sentences. Always ask yes/no questions."
        elif level == 'intermediate':
            rephrase_rule = "Only rephrase very short answers (1-2 words) or obvious errors."
            response_rule = "Use varied vocabulary, ask open questions."
        else:  # advanced
            rephrase_rule = "Rarely rephrase - only for major errors."
            response_rule = "Natural conversation, discuss complex topics."
        
        # This is the current prompt structure
        prompt = f"""You help {user_data.get('username', 'the student')} practice {learning_lang}.

{context_str}

LEVEL: {level}
RULES: {rephrase_rule} {response_rule}

RESPOND WITH JSON:
{{
  "rephrase": "complete sentence version (only if needed)",
  "response": "your reply in {learning_lang}",
  "include_rephrase": true/false
}}

Student said: "{message}"
Be concise and natural."""

        return prompt
    
    def test_token_limits(self, user_id, message_content):
        """Test different token limits to see impact on performance"""
        print(f"\n🎯 TOKEN LIMIT TESTING")
        print(f"=" * 40)
        
        user_data = find_user_by_id(user_id)
        minimal_prompt = self._build_minimal_prompt(user_data, message_content)
        
        token_limits = [50, 100, 150, 200, 300]
        
        for max_tokens in token_limits:
            print(f"\n🧪 Testing {max_tokens} token limit...")
            
            try:
                start_time = datetime.now()
                response = llm_manager.generate_chat_response(
                    messages=[
                        {"role": "system", "content": minimal_prompt},
                        {"role": "user", "content": message_content}
                    ],
                    temperature=0.7,
                    max_tokens=max_tokens,
                    log_request=False
                )
                duration = (datetime.now() - start_time).total_seconds() * 1000
                
                print(f"   ⚡ {max_tokens} tokens: {duration:.0f}ms")
                print(f"   Response length: {len(response)} chars")
                
            except Exception as e:
                print(f"   ❌ {max_tokens} tokens failed: {e}")
        
        print(f"\n💡 RECOMMENDATION: Use lowest token limit that gives good responses")

# Create debug route in chat.py
def debug_prompt_analysis(user_id, message="yes"):
    """Add this to chat.py as a new route"""
    debug_service = DebugChatService()
    return debug_service.analyze_prompt_content(user_id, message)