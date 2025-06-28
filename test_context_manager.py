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
    
    print("\n5. Testing configurable weights...")
    test_configurable_weights(context_mgr, channel)
    
    print("\n✅ Context manager test completed!")

def test_configurable_weights(context_mgr, channel):
    """Test how different weight configurations affect relevance scoring"""
    print("🔧 Testing Configurable Relevance Weights")
    print("-" * 50)
    
    # Test query
    query = "How do I fix Python AttributeError?"
    
    # Get current config values
    config = context_mgr.config
    print(f"Current weight configuration:")
    print(f"  Keyword overlap: {config.WEIGHT_KEYWORD_OVERLAP}")
    print(f"  Technical keywords: {config.WEIGHT_TECHNICAL_KEYWORDS}")
    print(f"  Question context: {config.WEIGHT_QUESTION_CONTEXT}")
    print(f"  Bot interaction: {config.WEIGHT_BOT_INTERACTION}")
    print(f"  Recency bonus: {config.WEIGHT_RECENCY_BONUS}")
    print(f"  URL bonus: {config.WEIGHT_URL_BONUS}")
    print(f"  Short message penalty: {config.PENALTY_SHORT_MESSAGE}")
    
    # Test relevance scoring on existing messages
    if channel in context_mgr.message_queues:
        messages = list(context_mgr.message_queues[channel])
        if messages:
            print(f"\nTesting relevance scores for query: '{query}'")
            for msg in messages:
                score = context_mgr._calculate_relevance_score(query, msg)
                print(f"  Score: {score:.3f} - {msg.user}: {msg.content[:60]}{'...' if len(msg.content) > 60 else ''}")
    
    print("\n💡 Weight Tuning Examples for Different Communities:")
    print()
    print("TECHNICAL communities (programming, DevOps):")
    print("  WEIGHT_TECHNICAL_KEYWORDS=0.5")
    print("  WEIGHT_KEYWORD_OVERLAP=0.3")
    print("  WEIGHT_QUESTION_CONTEXT=0.15")
    print()
    print("GENERAL chat communities:")
    print("  WEIGHT_KEYWORD_OVERLAP=0.5")
    print("  WEIGHT_QUESTION_CONTEXT=0.2")
    print("  WEIGHT_RECENCY_BONUS=0.15")
    print()
    print("SUPPORT channels (Q&A focused):")
    print("  WEIGHT_QUESTION_CONTEXT=0.4")
    print("  WEIGHT_BOT_INTERACTION=0.2")
    print("  WEIGHT_KEYWORD_OVERLAP=0.3")

if __name__ == "__main__":
    test_context_manager()
