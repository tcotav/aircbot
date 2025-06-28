#!/usr/bin/env python3
"""
Test script for OpenAI integration with environment variable support and daily rate limiting
"""

import os
import sys
import importlib
from llm_handler import LLMHandler

def reload_config():
    """Reload the config module to pick up environment changes"""
    if 'config' in sys.modules:
        importlib.reload(sys.modules['config'])
    from config import Config
    return Config()

def test_environment_variable():
    """Test that OpenAI API key is being read from environment"""
    print("🔐 Testing Environment Variable Configuration")
    print("=" * 50)
    
    config = reload_config()
    
    if config.OPENAI_API_KEY:
        print(f"✅ OpenAI API Key found: {config.OPENAI_API_KEY[:20]}...")
        print(f"✅ OpenAI Auto-enabled: {config.OPENAI_ENABLED}")
        print(f"✅ Daily limit: {config.OPENAI_DAILY_LIMIT}")
    else:
        print("❌ No OpenAI API key found in environment")
        return False
    
    print()
    return True

def test_real_openai_request():
    """Test a real OpenAI API request"""
    print("🤖 Testing Real OpenAI API Request")
    print("=" * 40)
    
    # Set up OpenAI-only mode
    os.environ['LLM_MODE'] = 'openai_only'
    os.environ['OPENAI_ENABLED'] = 'true'
    
    config = reload_config()
    llm = LLMHandler(config)
    
    print(f"Mode: {llm.mode}")
    print(f"OpenAI client available: {llm.openai_client is not None}")
    
    # Test a simple request
    print("\nMaking API request: 'What is 5+5?'")
    response = llm.ask_llm("What is 5+5?")
    print(f"Response: {response}")
    
    # Show usage stats
    if llm.openai_rate_limiter:
        usage = llm.openai_rate_limiter.get_usage_stats()
        print(f"Daily usage: {usage['today_usage']}/{usage['daily_limit']}")
    
    print()
    return response

def test_daily_rate_limiting():
    """Test the daily rate limiting functionality"""
    print("⏱️ Testing Daily Rate Limiting")
    print("=" * 35)
    
    # Set a very low daily limit for testing
    os.environ['LLM_MODE'] = 'openai_only'
    os.environ['OPENAI_ENABLED'] = 'true'
    os.environ['OPENAI_DAILY_LIMIT'] = '3'  # Low limit for testing
    
    config = reload_config()
    llm = LLMHandler(config)
    
    print(f"Testing with daily limit: {config.OPENAI_DAILY_LIMIT}")
    
    # Check current usage
    if llm.openai_rate_limiter:
        usage = llm.openai_rate_limiter.get_usage_stats()
        print(f"Current usage: {usage['today_usage']}/{usage['daily_limit']}")
        
        remaining = usage['daily_limit'] - usage['today_usage']
        
        if remaining > 0:
            print(f"\\nMaking {remaining} more request(s) to test rate limiting...")
            
            for i in range(remaining + 1):  # +1 to trigger rate limit
                question = f"What is {i+1}*2?"
                print(f"Request {i+1}: {question}")
                response = llm.ask_llm(question)
                print(f"Response: {response}")
                
                if "Daily OpenAI usage limit reached" in response:
                    print("✅ Rate limiting triggered successfully!")
                    break
        else:
            print("Already at daily limit - testing rate limit response...")
            response = llm.ask_llm("What is 10+10?")
            print(f"Rate limited response: {response}")
            
            if "Daily OpenAI usage limit reached" in response:
                print("✅ Rate limiting working correctly!")
    
    print()

def test_fallback_mode():
    """Test fallback mode with both services"""
    print("🔄 Testing Fallback Mode")
    print("=" * 25)
    
    # Set up fallback mode with normal limits
    os.environ['LLM_MODE'] = 'fallback'
    os.environ['LLM_ENABLED'] = 'true'
    os.environ['OPENAI_ENABLED'] = 'true'
    os.environ['OPENAI_DAILY_LIMIT'] = '100'  # Normal limit
    
    config = reload_config()
    llm = LLMHandler(config)
    
    print(f"Mode: {llm.mode}")
    print(f"Local client: {'✅' if llm.local_client else '❌'}")
    print(f"OpenAI client: {'✅' if llm.openai_client else '❌'}")
    
    # Test a simple question (should use local)
    print("\\nTesting simple question (should use local AI):")
    response = llm.ask_llm("What color is the sky?")
    print(f"Response: {response}")
    
    # Check which service was used
    stats = llm.get_performance_stats()
    local_requests = stats['local']['total_requests']
    openai_requests = stats['openai']['total_requests']
    
    print(f"Local requests: {local_requests}")
    print(f"OpenAI requests: {openai_requests}")
    
    if local_requests > openai_requests:
        print("✅ Local AI was used as expected")
    elif openai_requests > 0:
        print("ℹ️ OpenAI was used (fallback triggered)")
    
    print()

def test_performance_display():
    """Test the performance stats display"""
    print("📊 Testing Performance Stats Display")
    print("=" * 38)
    
    config = reload_config()
    llm = LLMHandler(config)
    
    stats = llm.get_performance_stats()
    
    print(f"Mode: {stats['mode']}")
    
    for client_type in ['local', 'openai']:
        client_stats = stats[client_type]
        if client_stats['enabled']:
            total_requests = client_stats['total_requests']
            
            if total_requests == 0:
                line = f"• {client_type.title()}: No requests yet"
            else:
                success_rate = client_stats['success_rate']
                avg_time = client_stats['avg_response_time']
                line = f"• {client_type.title()}: {total_requests} requests, {success_rate} success, avg: {avg_time}"
            
            # Add daily usage for OpenAI
            if client_type == 'openai' and 'daily_usage' in client_stats:
                daily_usage = client_stats['daily_usage']
                daily_limit = client_stats['daily_limit']
                daily_remaining = client_stats['daily_remaining']
                line += f" | Daily: {daily_usage}/{daily_limit} (remaining: {daily_remaining})"
            
            print(line)
    
    overall = stats['overall']
    print(f"• Overall: {overall['total_requests']} total, {overall['total_failed']} failed")
    print()

def main():
    """Run all tests"""
    print("🧪 OpenAI Integration Test Suite with Environment Variables")
    print("=" * 60)
    print()
    
    # Test 1: Environment variable configuration
    if not test_environment_variable():
        print("❌ Environment variable test failed - skipping other tests")
        return
    
    # Test 2: Real OpenAI request
    try:
        test_real_openai_request()
    except Exception as e:
        print(f"❌ OpenAI request failed: {e}")
    
    # Test 3: Daily rate limiting
    try:
        test_daily_rate_limiting()
    except Exception as e:
        print(f"❌ Rate limiting test failed: {e}")
    
    # Test 4: Fallback mode
    try:
        test_fallback_mode()
    except Exception as e:
        print(f"❌ Fallback mode test failed: {e}")
    
    # Test 5: Performance display
    try:
        test_performance_display()
    except Exception as e:
        print(f"❌ Performance display test failed: {e}")
    
    print("✅ All tests completed!")
    print()
    print("💡 Key Benefits:")
    print("• 🔐 Secure: API key from environment variables")
    print("• 💰 Cost Control: Daily rate limiting")
    print("• 🔄 Smart Fallback: Local → OpenAI when needed")
    print("• 📊 Monitoring: Detailed usage statistics")
    print("• ⚙️ Auto-config: Enables OpenAI when key is present")

if __name__ == '__main__':
    main()
