#!/usr/bin/env python3
"""
Debug script to test the full LLM pipeline with simple questions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_handler import LLMHandler
from config import Config
import logging

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_llm_pipeline():
    """Test the full LLM pipeline with simple questions"""
    
    config = Config()
    llm = LLMHandler(config)
    
    if not llm.is_enabled():
        print("❌ LLM is not enabled - check your configuration")
        return
    
    # Test cases that should get friendly responses
    test_questions = [
        "how are you today?",
        "hi there!",
        "what's up?",
        "good morning",
        "how's it going?",
        "hey bubba",
        "are you doing well?",
        "hello!",
        "how are things?",
        "nice to meet you"
    ]
    
    print("Testing full LLM pipeline with simple questions...\n")
    
    for i, question in enumerate(test_questions, 1):
        print(f"=== Test {i}: '{question}' ===")
        
        try:
            response = llm.ask_llm(question)
            
            if response:
                is_fallback = response == "That's too complicated to answer here"
                status = "❌ FALLBACK" if is_fallback else "✅ SUCCESS"
                print(f"{status} Response: '{response}'")
            else:
                print("❌ No response received")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()

if __name__ == "__main__":
    test_llm_pipeline()
