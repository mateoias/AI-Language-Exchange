#!/usr/bin/env python3
"""
Test script for the simplified chat service
"""
import requests
import json
import time


#!/usr/bin/env python3
"""
Optimized test script for the simplified chat service
Tests both with and without audio to isolate performance issues
"""
# Configuration - UPDATE THESE
EMAIL = "mateoias@hotmail.com"
PASSWORD = "1117"  
BASE_URL = "http://localhost:5000/api"

def get_token():
    """Login and get JWT token"""
    print("🔑 Getting authentication token...")
    
    login_data = {
        "email": EMAIL,
        "password": PASSWORD,
        "nativeLanguage": "English",
        "learningLanguage": "Spanish", 
        "proficiencyLevel": "beginner"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            print(f"✅ Got token: {token[:50]}...")
            return token
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_optimized_endpoint(token, message="yes", skip_audio=False):
    """Test the optimized chat endpoint"""
    audio_status = "disabled" if skip_audio else "enabled"
    print(f"\n🧪 Testing OPTIMIZED endpoint: '{message}' (audio {audio_status})")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "message": message,
        "audio_speed": 0.8,
        "skip_audio": skip_audio
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/chat/message-optimized", json=data, headers=headers)
        end_time = time.time()
        
        duration_ms = (end_time - start_time) * 1000
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Success! Total time: {duration_ms:.0f}ms")
            
            # Show performance breakdown
            if 'performance' in result:
                perf = result['performance']
                llm_time = perf.get('llm_time_ms', 0)
                audio_time = perf.get('audio_time_ms', 0)
                prompt_len = perf.get('prompt_length', 0)
                
                print(f"   🤖 LLM time: {llm_time:.0f}ms")
                print(f"   🎵 Audio time: {audio_time:.0f}ms")
                print(f"   📝 Prompt length: {prompt_len} chars")
            
            # Show segments
            print(f"   📊 Segments: {len(result.get('segments', []))}")
            for segment in result.get('segments', []):
                emoji = "🔧" if segment['type'] == 'rephrase' else "💬"
                print(f"      {emoji} {segment['type']}: {segment['text']}")
            
            return result
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Request error: {e}")
        return None

def test_llm_only(token, message="yes"):
    """Test pure LLM performance"""
    print(f"\n🧠 Testing LLM-ONLY performance: '{message}'")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {"message": message}
    
    try:
        response = requests.post(f"{BASE_URL}/chat/test-llm-only", json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            
            print("🧠 LLM-Only Comparison:")
            orig = result['llm_only_comparison']['original_estimated']
            opt = result['llm_only_comparison']['optimized']
            
            print(f"   Original (3 LLM calls): {orig['llm_time_ms']:.0f}ms")
            print(f"   Optimized (1 LLM call): {opt['llm_time_ms']:.0f}ms")
            print(f"   Prompt length: {opt['prompt_length']} chars")
            
            improvement = result['llm_only_comparison']['improvement']
            if improvement['percent_faster']:
                if improvement['percent_faster'] > 0:
                    print(f"   🚀 {improvement['percent_faster']:.1f}% faster!")
                else:
                    print(f"   🐌 {abs(improvement['percent_faster']):.1f}% slower")
            
            return result
        else:
            print(f"❌ LLM test failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ LLM test error: {e}")
        return None

def test_quick_comparison(token, message="yes"):
    """Test quick comparison"""
    print(f"\n⚡ Quick comparison: '{message}'")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {"message": message}
    
    try:
        response = requests.post(f"{BASE_URL}/chat/quick-comparison", json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            
            print("⚡ Quick Comparison Results:")
            orig_time = result['original']['total_time_ms']
            opt_time = result['optimized_no_audio']['total_time_ms']
            
            print(f"   Original (with audio): {orig_time:.0f}ms")
            print(f"   Optimized (no audio): {opt_time:.0f}ms")
            
            if result['improvement_percent']:
                improvement = result['improvement_percent']
                if improvement > 0:
                    print(f"   🚀 {improvement:.1f}% faster!")
                else:
                    print(f"   🐌 {abs(improvement):.1f}% slower")
            
            return result
        else:
            print(f"❌ Comparison failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Comparison error: {e}")
        return None

def main():
    print("🚀 OPTIMIZED Chat Service Test Script")
    print("=" * 50)
    
    # Get token
    token = get_token()
    if not token:
        return
    
    # Test messages
    test_messages = ["yes", "soccer", "I like pizza"]
    
    print(f"\n📋 Testing optimized endpoint WITHOUT audio...")
    for message in test_messages:
        test_optimized_endpoint(token, message, skip_audio=True)
        time.sleep(0.5)
    
    print(f"\n📋 Testing optimized endpoint WITH audio...")
    for message in test_messages[:2]:  # Just first 2 for audio test
        test_optimized_endpoint(token, message, skip_audio=False)
        time.sleep(0.5)
    
    print(f"\n📋 Testing LLM-only performance...")
    test_llm_only(token, "yes")
    
    print(f"\n📋 Testing quick comparison...")
    test_quick_comparison(token, "yes")
    
    print("\n✅ All optimized tests completed!")
    
    print("\n💡 To test manually:")
    print(f"export TOKEN='{token}'")
    print()
    print("# Test optimized without audio:")
    print("curl -X POST http://localhost:5000/api/chat/message-optimized \\")
    print('  -H "Authorization: Bearer $TOKEN" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"message": "yes", "skip_audio": true}\'')
    print()
    print("# Test quick comparison:")
    print("curl -X POST http://localhost:5000/api/chat/quick-comparison \\")
    print('  -H "Authorization: Bearer $TOKEN" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"message": "yes"}\'')

if __name__ == "__main__":
    main()