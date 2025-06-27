#!/usr/bin/env python3
"""
Test the complete LLM ask flow to debug the "too complicated" issue
"""

import sys
import os

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from llm_handler import LLMHandler

def test_ask_flow():
    """Test the complete ask flow like the bot would use"""
    
    print("🤖 Testing Complete LLM Ask Flow...")
    print()
    
    config = Config()
    llm = LLMHandler(config)
    
    if not llm.is_enabled():
        print("❌ LLM not available - skipping test")
        return
    
    # Test the same questions using the ask_llm method (which is what the bot uses)
    test_questions = [
        "how are you today?",
        "what's your name?", 
        "hello",
        "how's the weather?",
        "what time is it?",
        "tell me a joke",
        "explain quantum physics in detail",  # This should be rejected
    ]
    
    for question in test_questions:
        print(f"Question: '{question}'")
        
        # Use the actual ask_llm method that the bot calls
        response = llm.ask_llm(question)
        
        print(f"  Bot response: '{response}'")
        print()

def test_validation_edge_cases():
    """Test edge cases in validation"""
    
    print("🔬 Testing Validation Edge Cases...")
    print()
    
    config = Config()
    llm = LLMHandler(config)
    
    # Test various response patterns
    test_responses = [
        "I'm doing great!",  # Simple, should pass
        "I'm doing great! How are you?",  # Two sentences, should pass
        "I'm doing great! How are you? What's up?",  # Three sentences, should still pass with new rules
        "I'm doing great! How are you? What's up? How's work?",  # Four sentences, should fail
        "Here's a list:\n1. Item one\n2. Item two",  # List, should fail
        "Let me explain: first, you need to understand the basics. Then, you can move on to advanced topics.",  # Complex, should fail
        "That's a simple question.",  # Simple, should pass
    ]
    
    for response in test_responses:
        print(f"Testing: '{response}'")
        validated = llm._validate_response_length(response)
        status = "✅ PASS" if validated == response else "❌ FAIL"
        print(f"  {status} -> '{validated}'")
        print()

if __name__ == "__main__":
    test_ask_flow()
    test_validation_edge_cases()
