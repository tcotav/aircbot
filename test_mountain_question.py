#!/usr/bin/env python3
"""
Test the mountain ranges question specifically
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_handler import LLMHandler
from config import Config

def test_mountain_question():
    """Test the exact question from the issue"""
    
    config = Config()
    llm = LLMHandler(config)
    
    if not llm.is_enabled():
        print("❌ LLM is not enabled or available")
        return
    
    print("Testing mountain ranges question...")
    
    # Test multiple variations
    questions = [
        "name three mountain ranges in the continental united states",
        "what are three mountain ranges in the US?",
        "list 3 mountain ranges in america",
        "tell me three mountain ranges in the continental US"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{i}. Question: '{question}'")
        response = llm.ask_llm(question)
        print(f"   Response: '{response}'")
        
        # Check if it's a fallback response
        if "I'm not sure how to respond" in response or "too complicated" in response:
            print("   ❌ Got fallback response!")
        else:
            print("   ✅ Got proper response!")

if __name__ == "__main__":
    test_mountain_question()
