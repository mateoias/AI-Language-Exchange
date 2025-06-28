#!/usr/bin/env python3
"""
Test RAW OpenAI API performance to isolate the issue
"""
import openai
import time
import os
import sys

def test_raw_openai():
    """Test OpenAI API directly without any of your service layers"""
    print("🧪 RAW OPENAI API TEST")
    print("=" * 40)
    
    # Get API key from environment or config
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        print("💡 Add to your .env file or export OPENAI_API_KEY=your_key")
        return
    
    print(f"✅ API Key found: {api_key[:20]}...")
    
    # Create OpenAI client
    client = openai.OpenAI(api_key=api_key)
    
    # Test different models
    models_to_test = [
        {"name": "gpt-4o-mini", "description": "Should be fastest"},
        {"name": "gpt-3.5-turbo", "description": "Also fast"},
        {"name": "gpt-4", "description": "Slower but higher quality"}
    ]
    
    test_prompt = "Help student practice Spanish. Reply briefly: Hello"
    
    for model_config in models_to_test:
        model_name = model_config["name"]
        description = model_config["description"]
        
        print(f"\n🤖 Testing {model_name} ({description})")
        
        try:
            start_time = time.time()
            
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are helpful. Be brief."},
                    {"role": "user", "content": test_prompt}
                ],
                temperature=0.7,
                max_tokens=50
            )
            
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            response_text = response.choices[0].message.content.strip()
            
            print(f"   ⚡ Duration: {duration_ms:.0f}ms")
            print(f"   📝 Response: {response_text}")
            
            # Evaluate performance
            if duration_ms < 300:
                print("   🎯 EXCELLENT: Very fast!")
            elif duration_ms < 500:
                print("   ✅ GOOD: Acceptable speed")
            elif duration_ms < 800:
                print("   ⚠️  SLOW: Could be better")
            else:
                print("   🚨 VERY SLOW: Check network/region")
                
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
    
    return True

def test_current_config():
    """Test what your current llm_manager.py is actually using"""
    print(f"\n🔧 TESTING YOUR CURRENT CONFIG")
    print("=" * 40)
    
    try:
        # Try to import your LLM manager
        sys.path.append('/Users/imacmattimacmatt/Desktop/AI-Language-Exchange/server')
        from services.llm_manager import llm_manager
        
        print("✅ Successfully imported your llm_manager")
        
        # Test with your actual service
        print("🧪 Testing your llm_manager with minimal prompt...")
        
        start_time = time.time()
        
        response = llm_manager.generate_chat_response(
            messages=[
                {"role": "system", "content": "Be brief."},
                {"role": "user", "content": "Hello"}
            ],
            temperature=0.7,
            max_tokens=50,
            log_request=True  # This will show us what model is being used!
        )
        
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        print(f"⚡ Your service duration: {duration_ms:.0f}ms")
        print(f"📝 Response: {response}")
        
        if duration_ms > 800:
            print("🚨 YOUR SERVICE IS SLOW - Check the logged model name above!")
            print("💡 Look for the model name in the console output")
        else:
            print("✅ Your service speed is acceptable")
            
    except Exception as e:
        print(f"❌ Could not test your service: {e}")
        print("💡 Make sure you're in the right directory")

def check_network_latency():
    """Check basic network latency to OpenAI"""
    print(f"\n🌐 NETWORK LATENCY CHECK")
    print("=" * 30)
    
    try:
        import requests
        
        print("Testing network latency to OpenAI...")
        
        start_time = time.time()
        response = requests.get("https://api.openai.com/v1/models", timeout=10)
        end_time = time.time()
        
        latency_ms = (end_time - start_time) * 1000
        
        print(f"⚡ Network latency: {latency_ms:.0f}ms")
        
        if latency_ms < 100:
            print("✅ Excellent network connection")
        elif latency_ms < 300:
            print("✅ Good network connection")
        elif latency_ms < 500:
            print("⚠️  Slow network connection")
        else:
            print("🚨 Very slow network - this could be your issue!")
            
    except Exception as e:
        print(f"❌ Network test failed: {e}")

def main():
    print("🚀 RAW OPENAI PERFORMANCE DIAGNOSIS")
    print("=" * 60)
    
    # Test 1: Raw OpenAI API
    test_raw_openai()
    
    # Test 2: Your current config
    test_current_config()
    
    # Test 3: Network latency
    check_network_latency()
    
    print("\n🎯 WHAT TO LOOK FOR:")
    print("1. Raw gpt-4o-mini should be < 400ms")
    print("2. Your service should show the model name in logs")
    print("3. Network latency should be < 300ms")
    
    print("\n💡 IF RAW API IS FAST BUT YOUR SERVICE IS SLOW:")
    print("   - Your llm_manager has configuration issues")
    print("   - Check what model is actually being used")
    print("   - Look for the model name in console output")
    
    print("\n💡 IF RAW API IS ALSO SLOW:")
    print("   - Network/region issue with OpenAI")
    print("   - Try different OpenAI endpoint")
    print("   - Check your internet connection")

if __name__ == "__main__":
    main()