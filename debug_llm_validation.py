#!/usr/bin/env python3
"""
Test LLM response validation to debug the "too complicated" issue
"""

import sys
import os
import re

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from llm_handler import LLMHandler

def test_simple_questions():
    """Test simple questions that should work"""
    
    print("🧠 Testing LLM Response Validation...")
    print()
    
    config = Config()
    llm = LLMHandler(config)
    
    if not llm.is_enabled():
        print("❌ LLM not available - skipping test")
        return
    
    # Test simple questions that should get simple answers
    test_questions = [
        "how are you today?",
        "what's your name?", 
        "hello",
        "how's the weather?",
        "what time is it?",
        "tell me a joke",
    ]
    
    for question in test_questions:
        print(f"Question: '{question}'")
        
        # Get raw response first
        try:
            response = llm.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant in an IRC channel. IMPORTANT: Keep responses very short - maximum 2 sentences."},
                    {"role": "user", "content": question}
                ],
                max_tokens=config.LLM_MAX_TOKENS,
                temperature=config.LLM_TEMPERATURE,
            )
            
            raw_answer = response.choices[0].message.content.strip()
            print(f"  Raw LLM response: '{raw_answer}'")
            
            # Test validation
            validated = llm._validate_response_length(raw_answer)
            print(f"  After validation: '{validated}'")
            
            # Show validation details
            clean_response = re.sub(r'<think>.*?</think>', '', raw_answer, flags=re.DOTALL).strip()
            sentence_endings = clean_response.count('.') + clean_response.count('!') + clean_response.count('?')
            
            print(f"  Length: {len(clean_response)} chars, Sentences: {sentence_endings}")
            
            complexity_indicators = [
                clean_response.count('\n') > 1,  # Multiple paragraphs
                clean_response.count('1.') > 0 or clean_response.count('•') > 0,  # Lists
                clean_response.count(':') > 2,  # Multiple explanations
            ]
            
            if any(complexity_indicators):
                print(f"  Complexity indicators triggered: {complexity_indicators}")
            
        except Exception as e:
            print(f"  Error: {e}")
        
        print()

if __name__ == "__main__":
    test_simple_questions()
