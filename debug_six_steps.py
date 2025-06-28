#!/usr/bin/env python3
"""
Debug the six step validation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_handler import LLMHandler
from config import Config
import re

def debug_six_steps():
    """Debug the six steps validation"""
    
    llm = LLMHandler(Config())
    
    test_response = "Here are the steps: 1. First 2. Second 3. Third 4. Fourth 5. Fifth 6. Sixth"
    
    print(f"Testing: '{test_response}'")
    print(f"Length: {len(test_response)}")
    print(f"Count of '1.' patterns: {test_response.count('1.')}")
    print(f"Count of all periods: {test_response.count('.')}")
    
    # Check sentence counting
    period_count = len(re.findall(r'(?<!\d)\.', test_response))
    sentence_endings = period_count + test_response.count('!') + test_response.count('?')
    print(f"Non-numbered periods: {period_count}")
    print(f"Total sentence endings: {sentence_endings}")
    
    # Check complexity indicators
    complexity_indicators = [
        test_response.count('\\n') > 2,  # Multiple paragraphs
        test_response.count('1.') > 5 or test_response.count('•') > 5,  # Long lists
        test_response.count(':') > 3,  # Many explanations
        any(word in test_response.lower() for word in ['however', 'furthermore', 'moreover', 'specifically', 'particularly']),  # Academic language
    ]
    
    print(f"Complexity indicators:")
    print(f"  Multiple paragraphs (>2 \\n): {complexity_indicators[0]}")
    print(f"  Long lists (>5 1. or >5 •): {complexity_indicators[1]} (count of '1.': {test_response.count('1.')})")
    print(f"  Many explanations (>3 :): {complexity_indicators[2]}")
    print(f"  Academic language: {complexity_indicators[3]}")
    print(f"  Any true: {any(complexity_indicators)}")
    
    result = llm._validate_response_length(test_response)
    print(f"Result: '{result}'")

if __name__ == "__main__":
    debug_six_steps()
