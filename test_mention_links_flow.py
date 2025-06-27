#!/usr/bin/env python3
"""
Test the complete flow of mention + link request handling
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot import AircBot

def test_mention_with_link_request():
    """Test that mentioning the bot with a link request triggers the right logic"""
    
    print("🧪 Testing complete mention + link request flow...\n")
    
    # Create a mock bot instance to test the logic
    bot = AircBot()
    
    # Test cases for name mentions with link requests
    test_cases = [
        ("hey bubba, show me the links", True, "recent links"),
        ("aircbot what links do you have", True, "recent links"),
        ("bot search for python links", True, "search"),
        ("bubba show me links by john", True, "by user"),
        ("aircbot links stats please", True, "stats"),
        ("bot show detailed links", True, "details"),
        ("hey bubba, what's the weather?", False, "ask llm"),
        ("aircbot tell me a joke", False, "ask llm"),
    ]
    
    for message, should_be_links, expected_action in test_cases:
        print(f"Testing: '{message}'")
        
        # Test if bot is mentioned
        is_mentioned = bot.is_bot_mentioned(message)
        print(f"  Bot mentioned: {is_mentioned}")
        
        if is_mentioned:
            # Extract clean message (remove bot name)
            clean_message = message
            for pattern in ["bubba", "aircbot", "bot"]:
                clean_message = clean_message.replace(pattern, "").replace(pattern.title(), "")
            clean_message = clean_message.strip(" ,:;!?")
            clean_message_lower = clean_message.lower()
            print(f"  Clean message: '{clean_message}'")
            
            # Test if asking for links
            is_asking_links = bot._is_asking_for_links(clean_message_lower)
            print(f"  Is asking for links: {is_asking_links}")
            print(f"  Expected to be links: {should_be_links}")
            
            status = "✅" if is_asking_links == should_be_links else "❌"
            print(f"  {status} Correct detection")
            
            if is_asking_links:
                print(f"  Would trigger: {expected_action}")
        
        print()

if __name__ == "__main__":
    test_mention_with_link_request()
