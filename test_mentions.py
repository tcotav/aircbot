#!/usr/bin/env python3
"""
Test bot name mention detection
"""

def test_name_detection():
    """Test the name mention detection logic"""
    
    # Simulate the bot's name detection with word boundaries
    def is_bot_mentioned(message: str, bot_names: list) -> bool:
        import re
        message_lower = message.lower()
        for name in bot_names:
            pattern = rf'\b{re.escape(name.lower())}\b'
            if re.search(pattern, message_lower):
                return True
        return False
    
    # Test cases
    bot_names = ["bubba", "bubba_", "aircbot", "bot"]
    
    test_messages = [
        ("Hey bubba, what's the weather?", True),
        ("bubba can you help me?", True),
        ("I think the bot is broken", True),
        ("aircbot please explain this", True),
        ("Just chatting with friends", False),
        ("BUBBA: what time is it?", True),
        ("Is the AircBot working?", True),
        ("Bot, tell me a joke", True),
        ("This is just a normal message", False),
        ("The robot is cool", False),  # 'robot' != 'bot'
    ]
    
    print("🤖 Testing bot name mention detection...\n")
    
    for message, expected in test_messages:
        result = is_bot_mentioned(message, bot_names)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{message}' -> {result} (expected {expected})")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_name_detection()
