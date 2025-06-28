#!/usr/bin/env python3
"""
Debug what responses are being rejected
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_handler import LLMHandler
from config import Config

def debug_responses():
    """Debug what responses are being rejected"""
    
    config = Config()
    llm = LLMHandler(config)
    
    if not llm.is_enabled():
        print("❌ LLM is not enabled")
        return
    
    # Monkey patch to see what's happening in validation
    original_validate = llm._validate_response_length
    
    def debug_validate(response):
        print(f"\n=== VALIDATION DEBUG ===")
        print(f"Raw response (first 200 chars): '{response[:200]}...'")
        
        result = original_validate(response)
        
        print(f"Validation result: '{result}'")
        
        if result.startswith("I'm not sure") or result.startswith("That's too complicated"):
            print("❌ RESPONSE WAS REJECTED")
        else:
            print("✅ RESPONSE WAS ACCEPTED")
        
        print("=========================\n")
        return result
    
    llm._validate_response_length = debug_validate
    
    question = "name three mountain ranges in the continental united states"
    print(f"Testing: '{question}'")
    
    for i in range(2):
        print(f"\n--- Attempt {i+1} ---")
        response = llm.ask_llm(question)
        print(f"Final response: '{response}'")

if __name__ == "__main__":
    debug_responses()
