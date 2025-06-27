#!/usr/bin/env python3
"""
Debug script to see raw LLM responses before validation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_handler import LLMHandler
from config import Config
from typing import Optional
import logging
import re

# Set up logging to see what's happening
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

class DebugLLMHandler(LLMHandler):
    """Debug version of LLMHandler that shows raw responses"""
    
    def ask_llm(self, question: str, context: Optional[str] = None) -> str:
        """Debug version that shows the raw response"""
        if not self.is_enabled():
            return "❌ LLM is not available"
        
        try:
            # Build the prompt (same as original)
            messages = []
            
            if context:
                messages.append({
                    "role": "system", 
                    "content": f"You are a friendly IRC bot named bubba. Here's some recent channel context:\n{context}\n\nBe conversational and helpful. Keep responses brief - 1-2 sentences max. For simple greetings and casual questions, give friendly short answers. Only say 'That's too complicated to answer here' for genuinely complex technical questions that would need long explanations."
                })
            else:
                messages.append({
                    "role": "system",
                    "content": "You are a friendly IRC bot named bubba. Be conversational and helpful. Keep responses brief - 1-2 sentences max. For simple greetings and casual questions, give friendly short answers. Only say 'That's too complicated to answer here' for genuinely complex technical questions that would need long explanations."
                })
            
            messages.append({
                "role": "user",
                "content": question
            })
            
            # Make the API call
            response = self.client.chat.completions.create(
                model=self.config.LLM_MODEL,
                messages=messages,
                max_tokens=self.config.LLM_MAX_TOKENS,
                temperature=self.config.LLM_TEMPERATURE,
                stream=False
            )
            
            raw_answer = response.choices[0].message.content.strip()
            print(f"\n📝 RAW LLM RESPONSE for '{question}':")
            print(f"   Length: {len(raw_answer)} chars")
            print(f"   Content: '{raw_answer}'")
            print(f"   Repr: {repr(raw_answer)}")
            
            # Show step-by-step validation
            validated_answer = self._debug_validate_response_length(raw_answer)
            
            return validated_answer
            
        except Exception as e:
            print(f"❌ Error calling LLM: {e}")
            return f"❌ Error calling LLM: {str(e)}"
    
    def _debug_validate_response_length(self, response: str) -> str:
        """Debug version that shows each step"""
        print(f"\n🔍 VALIDATION STEPS:")
        print(f"   Original: '{response}'")
        print(f"   Original length: {len(response)}")
        
        # Remove thinking tags more aggressively
        clean_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
        print(f"   After removing closed <think> tags: '{clean_response}'")
        
        # If <think> still exists, remove everything from the first <think> onwards
        if '<think>' in clean_response:
            clean_response = re.split(r'<think>', clean_response)[0].strip()
            print(f"   After removing unclosed <think>: '{clean_response}'")
        
        # Also remove any other model artifacts
        clean_response = re.sub(r'</?think[^>]*>', '', clean_response, flags=re.IGNORECASE).strip()
        print(f"   After removing all think artifacts: '{clean_response}'")
        
        # If response is empty after cleaning, return fallback
        if not clean_response:
            print(f"   ❌ Response is empty after cleaning!")
            return "I'm not sure how to respond to that."
        
        # Count sentences
        sentence_endings = clean_response.count('.') + clean_response.count('!') + clean_response.count('?')
        print(f"   Sentence endings: {sentence_endings}")
        print(f"   Length after cleaning: {len(clean_response)}")
        
        # Length check
        if sentence_endings > 3 or len(clean_response) > 400:
            print(f"   ❌ Too long: {sentence_endings} sentences, {len(clean_response)} chars")
            return "That's too complicated to answer here"
        
        # Complexity checks
        complexity_checks = {
            'multiple_paragraphs': clean_response.count('\n') > 2,
            'long_lists': clean_response.count('1.') > 1 or clean_response.count('•') > 2,
            'many_explanations': clean_response.count(':') > 3,
            'academic_language': any(word in clean_response.lower() for word in ['however', 'furthermore', 'moreover', 'specifically', 'particularly'])
        }
        
        print(f"   Complexity checks: {complexity_checks}")
        
        if any(complexity_checks.values()):
            print(f"   ❌ Failed complexity check")
            return "That's too complicated to answer here"
        
        print(f"   ✅ Validation passed!")
        return clean_response

def test_problematic_cases():
    """Test cases that are failing"""
    
    config = Config()
    llm = DebugLLMHandler(config)
    
    if not llm.is_enabled():
        print("❌ LLM is not enabled - check your configuration")
        return
    
    # Focus on the cases that were problematic
    test_questions = [
        "good morning",
        "how's it going?",
        "hey bubba",
        "are you doing well?",
        "how are things?",
        "nice to meet you",
    ]
    
    print("Testing problematic cases with detailed debugging...\n")
    
    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"Testing: '{question}'")
        print('='*60)
        
        response = llm.ask_llm(question)
        print(f"\n🎯 FINAL RESULT: '{response}'")

if __name__ == "__main__":
    test_problematic_cases()
