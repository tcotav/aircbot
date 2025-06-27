#!/usr/bin/env python3
"""
Comprehensive test for link requests in natural language
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

def test_comprehensive_link_requests():
    """Test comprehensive set of link request patterns"""
    
    print("🔗 Testing comprehensive link request patterns...\n")
    
    # Test cases covering natural ways people ask for links
    test_cases = [
        # Direct link requests with bot mention
        ("bubba, show me the links", True),
        ("aircbot what links do you have?", True),
        ("bot can you share some links?", True),
        ("hey bubba, any links today?", True),
        ("aircbot do you have any saved links?", True),
        
        # Search and filtering requests
        ("bubba search for python links", True),
        ("bot find me links about AI", True),
        ("aircbot show me links by john", True),
        ("bubba what links has alice shared?", True),
        
        # Stats and metadata requests
        ("bot show me links stats", True),
        ("aircbot links statistics please", True),
        ("bubba detailed links with timestamps", True),
        ("bot how many links do we have?", True),
        
        # Non-link requests (should not trigger)
        ("bubba what's the weather?", False),
        ("aircbot tell me a joke", False),
        ("bot how are you doing?", False),
        ("bubba explain quantum physics", False),
        ("aircbot I like the missing links game", False),  # "links" but not a request
        
        # Edge cases
        ("bubba, links?", True),  # Very short but valid
        ("bot recent links pls", True),
        ("aircbot any new links worth checking?", True),
        ("bubba I need some links for my project", True),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for message, expected_is_links in test_cases:
        # Test if bot is mentioned
        is_mentioned = is_bot_mentioned(message)
        
        if is_mentioned:
            # Extract clean message (remove bot name)
            clean_message = message
            for pattern in ["bubba", "aircbot", "bot"]:
                clean_message = clean_message.replace(pattern, "").replace(pattern.title(), "")
            clean_message = clean_message.strip(" ,:;!?")
            clean_message_lower = clean_message.lower()
            
            # Test if asking for links
            is_asking_links = is_asking_for_links(clean_message_lower)
            
            status = "✅" if is_asking_links == expected_is_links else "❌"
            print(f"{status} '{message}'")
            print(f"    Clean: '{clean_message_lower}'")
            print(f"    Detected as links request: {is_asking_links} (expected: {expected_is_links})")
            
            if is_asking_links == expected_is_links:
                passed += 1
        else:
            print(f"⚠️  '{message}' - Bot not mentioned")
        
        print()
    
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

if __name__ == "__main__":
    test_comprehensive_link_requests()
