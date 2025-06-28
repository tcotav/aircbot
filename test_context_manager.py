#!/usr/bin/env python3
"""
Test script for context manager functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from context_manager import ContextManager
from config import Config
import time

def test_context_manager():
    """Test the context manager with sample messages"""
    print("🧪 Testing Context Manager")
    print("=" * 50)
    
    # Initialize
    config = Config()
    context_mgr = ContextManager(config)
    
    channel = "#test"
    
    # Add some sample messages
    print("\n1. Adding sample messages...")
    
    # Technical conversation
    context_mgr.add_message("alice", channel, "I'm having trouble with my Python code")
    time.sleep(0.1)
    context_mgr.add_message("bob", channel, "What kind of error are you getting?")
    time.sleep(0.1)
    context_mgr.add_message("alice", channel, "It says 'AttributeError: NoneType object has no attribute split'")
    time.sleep(0.1)
    context_mgr.add_message("bob", channel, "Sounds like you're trying to call split() on None")
    time.sleep(0.1)
    
    # Unrelated messages
    context_mgr.add_message("charlie", channel, "What's for lunch today?")
    time.sleep(0.1)
    context_mgr.add_message("dave", channel, "I think it's pizza")
    time.sleep(0.1)
    
    # More technical discussion
    context_mgr.add_message("alice", channel, "How do I check if a variable is None before calling methods?")
    time.sleep(0.1)
    context_mgr.add_message("eve", channel, "You can use 'if var is not None:' or use the walrus operator")
    time.sleep(0.1)
    
    # Add some bot interactions
    context_mgr.add_message("alice", channel, "!ask How do I handle None values in Python?", is_command=True)
    time.sleep(0.1)
    context_mgr.add_message("frank", channel, "aircbot what's the best way to debug Python code?", is_bot_mention=True)
    
    print(f"Added {context_mgr.get_context_summary(channel)['total_messages']} messages")
    
    # Test queries
    test_queries = [
        "How do I fix AttributeError in Python?",
        "What should I eat for lunch?", 
        "How to handle None values in Python code?",
        "What's the best debugging approach?",
        "Tell me about pizza recipes"
    ]
    
    print("\n2. Testing context relevance...")
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        relevant = context_mgr.get_relevant_context(channel, query, max_messages=3)
        
        if relevant:
            print(f"   Found {len(relevant)} relevant messages:")
            for msg in relevant:
                age = time.time() - msg.timestamp
                indicators = []
                if msg.is_command:
                    indicators.append("cmd")
                if msg.is_bot_mention:
                    indicators.append("@bot")
                indicator_str = f" [{','.join(indicators)}]" if indicators else ""
                print(f"   • {msg.user}{indicator_str}: {msg.content}")
        else:
            print("   No relevant context found")
    
    print("\n3. Testing formatted context...")
    query = "How to debug Python AttributeError?"
    relevant = context_mgr.get_relevant_context(channel, query)
    formatted = context_mgr.format_context_for_llm(relevant)
    
    print(f"\nFormatted context for LLM:")
    print("-" * 40)
    print(formatted)
    print("-" * 40)
    
    print("\n4. Context summary:")
    summary = context_mgr.get_context_summary(channel)
    for key, value in summary.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Context manager test completed!")

if __name__ == "__main__":
    test_context_manager()
