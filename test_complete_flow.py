#!/usr/bin/env python3
"""
Test the complete flow of mention + link request handling (logic only)
"""

import sys
import os
import re

def is_bot_mentioned(message: str, bot_nick: str = "bubba") -> bool:
    """Check if the bot is mentioned in the message"""
    message_lower = message.lower()
    
    # Check for various mention patterns with word boundaries
    mention_patterns = [
        rf'\b{re.escape(bot_nick.lower())}\b',  # Current nick with word boundaries
        r'\baircbot\b',  # Bot name with word boundaries
        r'\bbot\b',  # Generic bot reference with word boundaries
    ]
    
    # Check if any of the patterns appear in the message
    for pattern in mention_patterns:
        if re.search(pattern, message_lower):
            return True
    
    return False

def is_asking_for_links(message: str) -> bool:
    """Check if the user is asking for links"""
    # Check for explicit compound phrases first (these are always link requests)
    explicit_phrases = [
        "saved links", "recent links", "show links", "get links", 
        "list links", "what links", "any links", "share links",
        "links you saved", "links you have", "links stats",
        "links statistics", "detailed links"
    ]
    
    for phrase in explicit_phrases:
        if phrase in message:
            return True
    
    # Check if message is just "links" or "links?" - treat as request
    stripped = message.strip(" ?!.,;:")
    if stripped == "links" or stripped == "link":
        return True
    
    # For single word "links", need to have action words AND proper context
    if "links" in message:
        action_words = ["show", "get", "give", "list", "what", "any", "have", "share", "find", "search", "stats", "statistics", "detailed", "need", "want"]
        has_action_word = any(word in message for word in action_words)
        
        if has_action_word:
            # Check for question/request patterns
            patterns = [
                r'(?:what|any|show|get|have|share|find|search|need|want).*\blinks?\b',
                r'\blinks?\b.*(?:you|saved|recent|have|stats|statistics|detailed)',
                r'(?:stats|statistics|detailed).*\blinks?\b'
            ]
            
            for pattern in patterns:
                if re.search(pattern, message):
                    return True
                    
    return False

def determine_links_action(message: str) -> str:
    """Determine what type of links action should be taken"""
    if any(word in message for word in ["search", "find", "look for"]):
        return "search"
    elif any(word in message for word in ["by", "from", "user", "shared by"]):
        return "by user"
    elif any(word in message for word in ["stats", "statistics", "count", "how many"]):
        return "stats"
    elif any(word in message for word in ["details", "detailed", "timestamps", "when"]):
        return "details"
    else:
        return "recent links"

def test_mention_with_link_request():
    """Test that mentioning the bot with a link request triggers the right logic"""
    
    print("🧪 Testing complete mention + link request flow...\n")
    
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
        ("bubba, do you have any saved links?", True, "recent links"),
        ("bot can you show recent links?", True, "recent links"),
    ]
    
    for message, should_be_links, expected_action in test_cases:
        print(f"Testing: '{message}'")
        
        # Test if bot is mentioned
        is_mentioned = is_bot_mentioned(message)
        print(f"  Bot mentioned: {is_mentioned}")
        
        if is_mentioned:
            # Extract clean message (remove bot name)
            clean_message = message
            for pattern in ["bubba", "aircbot", "bot"]:
                clean_message = clean_message.replace(pattern, "").replace(pattern.title(), "")
            clean_message = clean_message.strip(" ,:;!?")
            clean_message_lower = clean_message.lower()
            print(f"  Clean message: '{clean_message_lower}'")
            
            # Test if asking for links
            is_asking_links = is_asking_for_links(clean_message_lower)
            print(f"  Is asking for links: {is_asking_links}")
            print(f"  Expected to be links: {should_be_links}")
            
            status = "✅" if is_asking_links == should_be_links else "❌"
            print(f"  {status} Correct detection")
            
            if is_asking_links:
                action = determine_links_action(clean_message_lower)
                print(f"  Would trigger: {action}")
                action_status = "✅" if action == expected_action else "❌"
                print(f"  {action_status} Expected: {expected_action}")
        
        print()

if __name__ == "__main__":
    test_mention_with_link_request()
