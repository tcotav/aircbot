#!/usr/bin/env python3
"""
Debug the exact validation failure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_handler import LLMHandler
from config import Config
import re
from prompts import get_error_message

def debug_validation_failure():
    """Debug exactly where validation is failing"""
    
    # Test the exact validation logic manually
    test_response = '''<think>
Okay, the user asked for three mountain ranges in the continental United States. Let me start by recalling the major ones. The Rockies come to mind first—they're a prominent range stretching from Canada to Mexico, definitely part of the US. Then there's the Sierra Nevada in California, which is iconic with places like Yosemite and Mount Whitney. Don't forget the Cascades along the Pacific Northwest border, including parts of Washington and Oregon.

Wait, should I check if these are all within continental US? Rockies go from New Mexico to Alaska but their main part is west of the Great Plains, so yes. Sierra Nevada starts in California's central part, fully within the mainland. Cascades include sections in Washington and Oregon, which are definitely continental US states. 

The user might be a student doing homework or someone planning a trip looking for destinations. Maybe they need brief names without extra details. I should list three clear ones: Rockies, Sierra Nevada, and Cascades. Keep it simple since the query doesn't ask for more info.
</think>
Sure! Three major mountain ranges in the continental United States are the Rocky Mountains, the Sierra Nevada, and the Cascade Range.'''
    
    print("Testing validation logic step by step...")
    print(f"Original response length: {len(test_response)}")
    print()
    
    # Step 1: Remove thinking tags
    clean_response = re.sub(r'<think>.*?</think>', '', test_response, flags=re.DOTALL)
    print(f"1. After removing closed <think> tags:")
    print(f"   Length: {len(clean_response)}")
    print(f"   Content: '{clean_response[:100]}...'")
    
    # Step 2: Check for unclosed think tags
    if '<think>' in clean_response:
        clean_response = clean_response.split('<think>')[0]
        print(f"2. After removing unclosed <think>:")
        print(f"   Length: {len(clean_response)}")
        print(f"   Content: '{clean_response[:100]}...'")
    
    # Step 3: Remove any remaining think artifacts
    clean_response = re.sub(r'</?think[^>]*>', '', clean_response, flags=re.IGNORECASE)
    clean_response = clean_response.strip()
    print(f"3. After final cleanup:")
    print(f"   Length: {len(clean_response)}")
    print(f"   Content: '{clean_response}'")
    
    # Step 4: Check if empty
    if not clean_response:
        print("❌ Response is empty after cleaning!")
        print(f"Would return: '{get_error_message('no_response')}'")
        return
    
    # Step 5: Count sentences
    sentence_endings = clean_response.count('.') + clean_response.count('!') + clean_response.count('?')
    print(f"4. Sentence count check:")
    print(f"   Sentence endings: {sentence_endings}")
    print(f"   Length: {len(clean_response)}")
    
    if sentence_endings > 3 or len(clean_response) > 400:
        print(f"❌ Length check failed!")
        print(f"Would return: '{get_error_message('too_complex')}'")
        return
    
    # Step 6: Complexity checks
    complexity_indicators = [
        clean_response.count('\\n') > 2,  # Multiple paragraphs
        clean_response.count('1.') > 5 or clean_response.count('•') > 5,  # Long lists
        clean_response.count(':') > 3,  # Many explanations
        any(word in clean_response.lower() for word in ['however', 'furthermore', 'moreover', 'specifically', 'particularly']),  # Academic language
    ]
    
    print(f"5. Complexity checks:")
    print(f"   Multiple paragraphs (>2 \\n): {clean_response.count('\\n')} -> {clean_response.count('\\n') > 2}")
    print(f"   Long lists (>5 1. or >5 •): {clean_response.count('1.')} 1.'s, {clean_response.count('•')} •'s -> {clean_response.count('1.') > 5 or clean_response.count('•') > 5}")
    print(f"   Many explanations (>3 :): {clean_response.count(':')} -> {clean_response.count(':') > 3}")
    print(f"   Academic language: {any(word in clean_response.lower() for word in ['however', 'furthermore', 'moreover', 'specifically', 'particularly'])}")
    
    if any(complexity_indicators):
        print(f"❌ Complexity check failed!")
        print(f"Would return: '{get_error_message('too_complex')}'")
        return
    
    print("✅ All checks passed!")
    print(f"Would return: '{clean_response}'")
    
    # Now test with actual LLM handler
    print()
    print("Testing with actual LLM handler...")
    llm = LLMHandler(Config())
    
    # Monkey patch the validation method to be more verbose
    original_validate = llm._validate_response_length
    
    def debug_validate(response):
        print(f"DEBUG: Validating response: '{response[:100]}...'")
        result = original_validate(response)
        print(f"DEBUG: Validation result: '{result}'")
        return result
    
    llm._validate_response_length = debug_validate
    
    response = llm.ask_llm('name three mountain ranges in the continental united states')
    print(f"Final response: '{response}'")

if __name__ == "__main__":
    debug_validation_failure()
