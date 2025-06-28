#!/usr/bin/env python3
"""
Test script to demonstrate configurable relevance weights
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from context_manager import ContextManager
from config import Config
import time

def test_configurable_weights():
    """Test how different weight configurations affect relevance scoring"""
    print("🧪 Testing Configurable Relevance Weights")
    print("=" * 60)
    
    # Test with default weights
    print("\n1. Testing with DEFAULT weights:")
    config_default = Config()
    context_mgr_default = ContextManager(config_default)
    
    # Add test messages
    channel = "#test"
    context_mgr_default.add_message("alice", channel, "I'm having a Python error with my code")
    time.sleep(0.1)
    context_mgr_default.add_message("bob", channel, "What's for lunch today?")
    time.sleep(0.1)
    context_mgr_default.add_message("charlie", channel, "The AttributeError is common in Python")
    
    query = "How do I fix Python AttributeError?"
    relevant_default = context_mgr_default.get_relevant_context(channel, query)
    
    print(f"Query: '{query}'")
    print(f"Default weights - Found {len(relevant_default)} relevant messages:")
    for msg in relevant_default:
        score = context_mgr_default._calculate_relevance_score(query, msg)
        print(f"  • Score: {score:.3f} - {msg.user}: {msg.content}")
    
    print(f"\nDefault weight configuration:")
    print(f"  Keyword overlap: {config_default.WEIGHT_KEYWORD_OVERLAP}")
    print(f"  Technical keywords: {config_default.WEIGHT_TECHNICAL_KEYWORDS}")
    print(f"  Question context: {config_default.WEIGHT_QUESTION_CONTEXT}")
    print(f"  Bot interaction: {config_default.WEIGHT_BOT_INTERACTION}")
    
    # Test with modified weights (emphasize technical keywords)
    print("\n" + "="*60)
    print("2. Testing with TECHNICAL-FOCUSED weights:")
    
    # Temporarily modify environment to test different weights
    os.environ['WEIGHT_KEYWORD_OVERLAP'] = '0.2'  # Reduced
    os.environ['WEIGHT_TECHNICAL_KEYWORDS'] = '0.6'  # Increased
    os.environ['WEIGHT_QUESTION_CONTEXT'] = '0.1'  # Reduced
    os.environ['WEIGHT_BOT_INTERACTION'] = '0.05'  # Reduced
    
    # Create new config with modified weights
    config_tech = Config()
    context_mgr_tech = ContextManager(config_tech)
    
    # Add the same test messages
    context_mgr_tech.add_message("alice", channel, "I'm having a Python error with my code")
    time.sleep(0.1)
    context_mgr_tech.add_message("bob", channel, "What's for lunch today?")
    time.sleep(0.1)
    context_mgr_tech.add_message("charlie", channel, "The AttributeError is common in Python")
    
    relevant_tech = context_mgr_tech.get_relevant_context(channel, query)
    
    print(f"Query: '{query}'")
    print(f"Technical-focused weights - Found {len(relevant_tech)} relevant messages:")
    for msg in relevant_tech:
        score = context_mgr_tech._calculate_relevance_score(query, msg)
        print(f"  • Score: {score:.3f} - {msg.user}: {msg.content}")
    
    print(f"\nTechnical-focused weight configuration:")
    print(f"  Keyword overlap: {config_tech.WEIGHT_KEYWORD_OVERLAP}")
    print(f"  Technical keywords: {config_tech.WEIGHT_TECHNICAL_KEYWORDS}")
    print(f"  Question context: {config_tech.WEIGHT_QUESTION_CONTEXT}")
    print(f"  Bot interaction: {config_tech.WEIGHT_BOT_INTERACTION}")
    
    # Reset environment
    del os.environ['WEIGHT_KEYWORD_OVERLAP']
    del os.environ['WEIGHT_TECHNICAL_KEYWORDS']
    del os.environ['WEIGHT_QUESTION_CONTEXT']
    del os.environ['WEIGHT_BOT_INTERACTION']
    
    print("\n" + "="*60)
    print("💡 Weight Tuning Examples:")
    print()
    print("For TECHNICAL communities (programming, DevOps):")
    print("  WEIGHT_TECHNICAL_KEYWORDS=0.5")
    print("  WEIGHT_KEYWORD_OVERLAP=0.3")
    print("  WEIGHT_QUESTION_CONTEXT=0.15")
    print()
    print("For GENERAL chat communities:")
    print("  WEIGHT_KEYWORD_OVERLAP=0.5")
    print("  WEIGHT_QUESTION_CONTEXT=0.2")
    print("  WEIGHT_RECENCY_BONUS=0.15")
    print()
    print("For SUPPORT channels (lots of Q&A):")
    print("  WEIGHT_QUESTION_CONTEXT=0.4")
    print("  WEIGHT_BOT_INTERACTION=0.2")
    print("  WEIGHT_KEYWORD_OVERLAP=0.3")
    
    print("\n✅ Configurable weights test completed!")

if __name__ == "__main__":
    test_configurable_weights()
