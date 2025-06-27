#!/usr/bin/env python3
"""
Debug script to test LLM validation with simple questions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_handler import LLMHandler
from config import Config
import re

def debug_validation(response: str) -> tuple[str, str]:
    """
    Debug the validation process step by step
    Returns: (final_result, debug_info)
    """
    debug_info = []
    debug_info.append(f"Original response: '{response}'")
    debug_info.append(f"Original length: {len(response)}")
    
    # Step 1: Remove thinking tags more aggressively
    clean_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
    debug_info.append(f"After removing closed <think> tags: '{clean_response}'")
    
    # If <think> still exists, remove everything from the first <think> onwards
    if '<think>' in clean_response:
        clean_response = re.split(r'<think>', clean_response)[0].strip()
        debug_info.append(f"After removing unclosed <think>: '{clean_response}'")
    
    # Also remove any other model artifacts
    clean_response = re.sub(r'</?think[^>]*>', '', clean_response, flags=re.IGNORECASE).strip()
    debug_info.append(f"After removing all think artifacts: '{clean_response}'")
    
    # If response is empty after cleaning, return fallback
    if not clean_response:
        debug_info.append("Response is empty after cleaning - returning fallback")
        return "I'm not sure how to respond to that.", "\n".join(debug_info)
    
    # Count sentences (rough approximation)
    sentence_endings = clean_response.count('.') + clean_response.count('!') + clean_response.count('?')
    debug_info.append(f"Sentence endings count: {sentence_endings}")
    debug_info.append(f"Character count: {len(clean_response)}")
    
    # Be more lenient - allow up to 3 sentences and 400 chars for simple conversations
    if sentence_endings > 3 or len(clean_response) > 400:
        debug_info.append("Response too long - failing validation")
        return "That's too complicated to answer here", "\n".join(debug_info)
    
    # Check for genuine complexity indicators that suggest technical explanations
    complexity_checks = {
        'multiple_paragraphs': clean_response.count('\n') > 2,
        'long_lists': clean_response.count('1.') > 1 or clean_response.count('•') > 2,
        'many_explanations': clean_response.count(':') > 3,
        'academic_language': any(word in clean_response.lower() for word in ['however', 'furthermore', 'moreover', 'specifically', 'particularly'])
    }
    
    debug_info.append("Complexity checks:")
    for check, result in complexity_checks.items():
        debug_info.append(f"  {check}: {result}")
    
    if any(complexity_checks.values()):
        debug_info.append("Failed complexity check - returning fallback")
        return "That's too complicated to answer here", "\n".join(debug_info)
    
    debug_info.append("Passed all checks - returning clean response")
    return clean_response, "\n".join(debug_info)

def test_simple_questions():
    """Test various simple questions that should pass validation"""
    
    # Test cases - these should all pass validation
    test_cases = [
        "I'm doing great, thanks for asking!",
        "Hi there! How can I help you today?",
        "Good morning! I'm here and ready to chat.",
        "That's a nice question. I'm fine, how about you?",
        "Hey! I'm doing well. What's up?",
        "I'm having a wonderful day, thank you!",
        "Pretty good! Just hanging out in the channel.",
        "All good here! Thanks for checking in.",
        "I'm great! Ready to help with anything you need.",
        "Doing fantastic! Hope you're having a good day too.",
        # Edge cases
        "Yes.",
        "No problem!",
        "Sounds good to me.",
        "That makes sense.",
        # Cases that might fail but shouldn't for casual chat
        "I'm doing really well today! The weather is nice and I'm enjoying chatting with everyone.",
        "Hey there! I'm good, thanks for asking. How are you doing today?",
        # Cases with punctuation
        "I'm great! How are you?",
        "Good morning! Hope you're well.",
        "Hi! I'm doing fine, thanks!",
    ]
    
    print("Testing simple question responses...\n")
    
    for i, response in enumerate(test_cases, 1):
        print(f"=== Test Case {i} ===")
        result, debug_info = debug_validation(response)
        
        passed = result != "That's too complicated to answer here"
        status = "✅ PASS" if passed else "❌ FAIL"
        
        print(f"{status} - Result: '{result}'")
        if not passed:
            print("DEBUG INFO:")
            print(debug_info)
        print()

if __name__ == "__main__":
    test_simple_questions()
