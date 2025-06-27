#!/usr/bin/env python3
"""
Quick test of a single question
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_handler import LLMHandler
from config import Config

def quick_test():
    """Test one question"""
    
    config = Config()
    llm = LLMHandler(config)
    
    if not llm.is_enabled():
        print("❌ LLM is not enabled")
        return
    
    question = "how are you today?"
    print(f"Testing: '{question}'")
    
    response = llm.ask_llm(question)
    print(f"Response: '{response}'")

if __name__ == "__main__":
    quick_test()
