#!/usr/bin/env python3
"""
Debug specific responses that are getting rejected
"""

import sys
import os
import re

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from llm_handler import LLMHandler

def debug_specific_responses():
    """Debug the specific responses that are being rejected"""
    
    print("🔍 Debugging Specific LLM Responses...")
    print()
    
    config = Config()
    llm = LLMHandler(config)
    
    if not llm.is_enabled():
        print("❌ LLM not available - skipping test")
        return
    
    # Test specific questions that are getting rejected
    problem_questions = [
        "what's your name?",
        "how's the weather?", 
        "what time is it?",
    ]
    
    for question in problem_questions:
        print(f"Question: '{question}'")
        
        # Get the raw response to see what's happening
        try:
            response = llm.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a friendly IRC bot named bubba. Be conversational and helpful. Keep responses brief - 1-2 sentences max. For simple greetings and casual questions, give friendly short answers. Only say 'That's too complicated to answer here' for genuinely complex technical questions that would need long explanations."},
                    {"role": "user", "content": question}
                ],
                max_tokens=config.LLM_MAX_TOKENS,
                temperature=config.LLM_TEMPERATURE,
            )
            
            raw_answer = response.choices[0].message.content.strip()
            print(f"  Raw LLM response: '{raw_answer}'")
            print(f"  Raw length: {len(raw_answer)}")
            
            # Test validation step by step
            clean_response = re.sub(r'<think>.*?</think>', '', raw_answer, flags=re.DOTALL).strip()
            print(f"  After cleaning: '{clean_response}'")
            print(f"  Clean length: {len(clean_response)}")
            
            sentence_endings = clean_response.count('.') + clean_response.count('!') + clean_response.count('?')
            print(f"  Sentence count: {sentence_endings}")
            
            if sentence_endings > 3 or len(clean_response) > 400:
                print(f"  ❌ REJECTED: Too many sentences ({sentence_endings}) or too long ({len(clean_response)} chars)")
            
            # Check complexity indicators
            complexity_checks = {
                'Multiple paragraphs': clean_response.count('\n') > 2,
                'Long lists': clean_response.count('1.') > 1 or clean_response.count('•') > 2,
                'Many explanations': clean_response.count(':') > 3,
                'Academic language': any(word in clean_response.lower() for word in ['however', 'furthermore', 'moreover', 'specifically', 'particularly']),
            }
            
            for check, result in complexity_checks.items():
                if result:
                    print(f"  ❌ REJECTED: {check}")
            
            validated = llm._validate_response_length(raw_answer)
            print(f"  Final result: '{validated}'")
            
        except Exception as e:
            print(f"  Error: {e}")
        
        print()

if __name__ == "__main__":
    debug_specific_responses()
