#!/usr/bin/env python3
"""
Test script for LLM integration
"""

from config import Config
from llm_handler import LLMHandler
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_llm():
    """Test LLM functionality"""
    print("🤖 Testing LLM integration...\n")
    
    config = Config()
    llm = LLMHandler(config)
    
    print(f"LLM Enabled: {llm.is_enabled()}")
    print(f"Base URL: {config.LLM_BASE_URL}")
    print(f"Model: {config.LLM_MODEL}")
    print()
    
    if llm.is_enabled():
        print("Testing simple question...")
        response = llm.ask_llm("What is the capital of France?")
        cleaned_response = clean_response_for_irc(response)
        print(f"Raw response: {response}")
        print(f"Cleaned response: {cleaned_response}")
        print()
        
        print("Testing complex question (should be rejected)...")
        complex_response = llm.ask_llm("Explain the entire history of computer programming languages and their evolution")
        cleaned_complex = clean_response_for_irc(complex_response)
        print(f"Complex response: {cleaned_complex}")
        print()
        
        print("Testing with context...")
        context = "[12:00] <alice> We're planning a trip to Europe\n[12:01] <bob> I love French cuisine"
        response = llm.ask_llm("What should we visit?", context)
        cleaned_response = clean_response_for_irc(response)
        print(f"Raw response: {response}")
        print(f"Cleaned response: {cleaned_response}")
    else:
        print("❌ LLM is not enabled or available")
        print("Make sure:")
        print("1. Ollama is running: ollama serve")
        print("2. You have a model: ollama pull deepseek-r1:latest")
        print("3. LLM_ENABLED=true in .env")

def clean_response_for_irc(response: str) -> str:
    """Clean LLM response for IRC compatibility"""
    import re
    # Remove thinking tags that some models include
    response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
    
    # Replace various newline characters with spaces
    response = response.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')
    
    # Replace multiple spaces with single spaces
    response = re.sub(r'\s+', ' ', response)
    
    # Strip leading/trailing whitespace
    response = response.strip()
    
    return response

if __name__ == "__main__":
    test_llm()
