#!/usr/bin/env python3
"""
Final test of the mountain ranges question
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_handler import LLMHandler
from config import Config

def final_test():
    """Final test of the mountain ranges question"""
    
    llm = LLMHandler(Config())
    
    if not llm.is_enabled():
        print("❌ LLM is not enabled")
        return
    
    question = "name three mountain ranges in the continental united states"
    print(f"Testing: '{question}'")
    
    # Test multiple times to see consistency
    for i in range(3):
        print(f"\nAttempt {i+1}:")
        response = llm.ask_llm(question)
        print(f"Response: '{response}'")
        
        if "I'm not sure how to respond" in response or "too complicated" in response:
            print("❌ Got fallback response")
        else:
            print("✅ Got proper response")

if __name__ == "__main__":
    final_test()
