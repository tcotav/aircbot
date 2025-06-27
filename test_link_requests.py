#!/usr/bin/env python3
"""
Test link request detection in name mentions
"""

import re

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

def test_link_detection():
    """Test the link request detection"""
    
    test_cases = [
        # Should detect as link requests
        ("show me the links", True),
        ("what links do you have", True), 
        ("get recent links", True),
        ("any saved links?", True),
        ("can you show links from bob", True),
        ("search for python links", True),
        ("what recent links are there", True),
        ("do you have any links", True),
        ("show me links you saved", True),
        ("links stats please", True),
        ("detailed links would be nice", True),
        ("show me links statistics", True),
        ("links?", True),
        ("need some links", True),
        ("want to see links", True),
        
        # Should NOT detect as link requests
        ("what's the weather like", False),
        ("tell me a joke", False),
        ("how are you doing", False),
        ("what time is it", False),
        ("I like missing links zelda game", False),  # Contains "links" but not a request (no action word directly with links)
        ("explain something", False),
    ]
    
    print("🔗 Testing link request detection...\n")
    
    for message, expected in test_cases:
        result = is_asking_for_links(message.lower())
        status = "✅" if result == expected else "❌"
        print(f"{status} '{message}' -> {result} (expected {expected})")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_link_detection()
