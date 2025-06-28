#!/usr/bin/env python3
"""
Debug the mountain ranges question specifically
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_handler import LLMHandler
from config import Config
import re

def debug_mountain_question():
    """Debug why the mountain ranges question is failing"""
    
    config = Config()
    llm = LLMHandler(config)
    
    if not llm.is_enabled():
        print("❌ LLM not available")
        return
    
    question = "name three mountain ranges in the continental united states"
    print(f"Testing question: '{question}'")
    print()
    
    try:
        # Build the prompt (same as in ask_llm)
        messages = []
        
        from prompts import get_system_prompt
        system_content = get_system_prompt(config.IRC_NICKNAME, None)
        messages.append({
            "role": "system",
            "content": system_content
        })
        
        messages.append({
            "role": "user",
            "content": question
        })
        
        # Make the API call
        response = llm.client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=messages,
            max_tokens=config.LLM_MAX_TOKENS,
            temperature=config.LLM_TEMPERATURE,
            stream=False
        )
        
        raw_answer = response.choices[0].message.content.strip()
        print(f"📝 RAW LLM RESPONSE:")
        print(f"   Length: {len(raw_answer)} chars")
        print(f"   Content: '{raw_answer}'")
        print(f"   Repr: {repr(raw_answer)}")
        print()
        
        # Debug the validation step by step
        print("🔍 VALIDATION STEPS:")
        
        # Remove thinking tags
        clean_response = re.sub(r'<think>.*?</think>', '', raw_answer, flags=re.DOTALL)
        print(f"1. After removing closed <think> tags: '{clean_response}'")
        
        if '<think>' in clean_response:
            clean_response = clean_response.split('<think>')[0]
            print(f"2. After removing unclosed <think>: '{clean_response}'")
        
        clean_response = re.sub(r'</?think[^>]*>', '', clean_response, flags=re.IGNORECASE)
        clean_response = clean_response.strip()
        print(f"3. After cleanup: '{clean_response}'")
        
        if not clean_response:
            print("❌ Response is empty after cleaning!")
            return
        
        # Count sentences
        sentence_endings = clean_response.count('.') + clean_response.count('!') + clean_response.count('?')
        print(f"4. Sentence endings: {sentence_endings}")
        print(f"5. Character length: {len(clean_response)}")
        
        if sentence_endings > 3 or len(clean_response) > 400:
            print(f"❌ Failed length check: {sentence_endings} sentences, {len(clean_response)} chars")
            return
        
        # Complexity checks
        complexity_checks = {
            'multiple_paragraphs': clean_response.count('\\n') > 2,
            'long_lists_1': clean_response.count('1.') > 5,
            'long_lists_bullet': clean_response.count('•') > 5,
            'many_explanations': clean_response.count(':') > 3,
            'academic_language': any(word in clean_response.lower() for word in ['however', 'furthermore', 'moreover', 'specifically', 'particularly'])
        }
        
        print(f"6. Complexity checks: {complexity_checks}")
        
        # Show counts for debugging
        print(f"   '1.' count: {clean_response.count('1.')}")
        print(f"   '•' count: {clean_response.count('•')}")
        print(f"   ':' count: {clean_response.count(':')}")
        print(f"   newline count: {clean_response.count('\\n')}")
        
        if any(complexity_checks.values()):
            print("❌ Failed complexity check")
            return
        
        print("✅ Should pass validation!")
        print(f"Final result: '{clean_response}'")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_mountain_question()
