#!/usr/bin/env python3
"""
Comprehensive test suite for AircBot
Consolidates all testing functionality into a single file.
"""

import sys
import os
import time
import re
import threading
from collections import defaultdict, deque

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot import AircBot

# Import bot components
from rate_limiter import RateLimiter

def run_all_tests():
    """Run all test suites"""
    print("🧪 AircBot Comprehensive Test Suite")
    print("=" * 50)
    print()
    
    # Run all test categories
    test_mention_detection()
    test_link_request_detection()
    test_rate_limiter()
    test_bot_integration()
    test_llm_validation()
    test_thinking_message_duplication()
    
    print("\n🎉 All tests completed!")

# ===== MENTION DETECTION TESTS =====

def is_bot_mentioned(message: str, bot_nick: str = "bubba") -> bool:
    """Check if the bot is mentioned in the message"""
    message_lower = message.lower()
    
    mention_patterns = [
        rf'\b{re.escape(bot_nick.lower())}\b',
        r'\baircbot\b',
        r'\bbot\b',
    ]
    
    for pattern in mention_patterns:
        if re.search(pattern, message_lower):
            return True
    return False

def test_mention_detection():
    """Test bot name mention detection"""
    print("🤖 Testing Bot Name Mention Detection...")
    
    test_cases = [
        ("Hey bubba, what's the weather?", True),
        ("bubba can you help me?", True),
        ("I think the bot is broken", True),
        ("aircbot please explain this", True),
        ("Just chatting with friends", False),
        ("BUBBA: what time is it?", True),
        ("Is the AircBot working?", True),
        ("Bot, tell me a joke", True),
        ("This is just a normal message", False),
        ("The robot is cool", False),
    ]
    
    passed = 0
    for message, expected in test_cases:
        result = is_bot_mentioned(message)
        status = "✅" if result == expected else "❌"
        if result != expected:
            print(f"{status} '{message}' -> {result} (expected {expected})")
        passed += (result == expected)
    
    print(f"✅ Mention detection: {passed}/{len(test_cases)} tests passed")
    print()

# ===== LINK REQUEST DETECTION TESTS =====

def is_asking_for_links(message: str) -> bool:
    """Check if the user is asking for links"""
    explicit_phrases = [
        "saved links", "recent links", "show links", "get links", 
        "list links", "what links", "any links", "share links",
        "links you saved", "links you have", "links stats",
        "links statistics", "detailed links"
    ]
    
    for phrase in explicit_phrases:
        if phrase in message:
            return True
    
    stripped = message.strip(" ?!.,;:")
    if stripped == "links" or stripped == "link":
        return True
    
    if "links" in message:
        action_words = ["show", "get", "give", "list", "what", "any", "have", "share", "find", "search", "stats", "statistics", "detailed", "need", "want"]
        has_action_word = any(word in message for word in action_words)
        
        if has_action_word:
            patterns = [
                r'(?:what|any|show|get|have|share|find|search|need|want).*\blinks?\b',
                r'\blinks?\b.*(?:you|saved|recent|have|stats|statistics|detailed)',
                r'(?:stats|statistics|detailed).*\blinks?\b'
            ]
            
            for pattern in patterns:
                if re.search(pattern, message):
                    return True
    return False

def test_link_request_detection():
    """Test link request detection"""
    print("🔗 Testing Link Request Detection...")
    
    test_cases = [
        # Should detect as link requests
        ("show me the links", True),
        ("what links do you have", True),
        ("get recent links", True),
        ("any saved links?", True),
        ("can you show links from bob", True),
        ("search for python links", True),
        ("links stats please", True),
        ("detailed links would be nice", True),
        ("links?", True),
        ("need some links", True),
        ("want to see links", True),
        
        # Should NOT detect as link requests
        ("what's the weather like", False),
        ("tell me a joke", False),
        ("how are you doing", False),
        ("I like missing links zelda game", False),
        ("explain something", False),
    ]
    
    passed = 0
    for message, expected in test_cases:
        result = is_asking_for_links(message.lower())
        status = "✅" if result == expected else "❌"
        if result != expected:
            print(f"{status} '{message}' -> {result} (expected {expected})")
        passed += (result == expected)
    
    print(f"✅ Link request detection: {passed}/{len(test_cases)} tests passed")
    print()

# ===== RATE LIMITER TESTS =====

def test_rate_limiter():
    """Test rate limiting functionality"""
    print("⏱️ Testing Rate Limiter...")
    
    # Test basic functionality
    limiter = RateLimiter(user_limit_per_minute=2, total_limit_per_minute=5)
    
    # User rate limiting
    assert limiter.is_allowed('alice') == True
    assert limiter.is_allowed('alice') == True
    assert limiter.is_allowed('alice') == False  # Third request blocked
    
    # Different user should work
    assert limiter.is_allowed('bob') == True
    assert limiter.is_allowed('bob') == True
    assert limiter.is_allowed('bob') == False
    
    # Total rate limiting (we've used 4/5 requests)
    assert limiter.is_allowed('charlie') == True  # 5th request
    assert limiter.is_allowed('diana') == False   # Total limit reached
    
    # Test stats
    stats = limiter.get_stats()
    assert stats['total_requests_this_minute'] == 5
    assert stats['active_users'] == 3
    
    user_stats = limiter.get_user_stats('alice')
    assert user_stats['requests_this_minute'] == 2
    assert user_stats['remaining'] == 0
    
    print("✅ Rate limiter: All tests passed")
    print()

# ===== BOT INTEGRATION TESTS =====

class MockConnection:
    def __init__(self):
        self.messages = []
        self.nickname = "bubba"
    
    def privmsg(self, channel, message):
        self.messages.append(f"[{channel}] {message}")
    
    def get_nickname(self):
        return self.nickname

def test_bot_integration():
    """Test bot integration with rate limiting"""
    print("🤖 Testing Bot Integration...")
    
    try:
        # Import bot after setting up mocks
        from bot import AircBot
        
        # Create bot instance
        bot = AircBot()
        bot.rate_limiter = RateLimiter(user_limit_per_minute=1, total_limit_per_minute=5)
        
        connection = MockConnection()
        channel = "#test"
        
        # Test that commands are rate limited
        bot.handle_command(connection, channel, "alice", "!help")
        initial_count = len(connection.messages)
        
        # Second command should be rate limited
        bot.handle_command(connection, channel, "alice", "!links")
        rate_limited_count = len(connection.messages)
        
        # Should have gotten a rate limit message
        assert rate_limited_count > initial_count, "Rate limit message should be sent"
        
        # Test name mentions
        bot.handle_name_mention(connection, channel, "bob", "bubba what links do you have?")
        mention_count = len(connection.messages)
        
        # Second mention should be rate limited
        bot.handle_name_mention(connection, channel, "bob", "aircbot tell me a joke")
        mention_limited_count = len(connection.messages)
        
        assert mention_limited_count > mention_count, "Rate limit message should be sent for mentions"
        
        print("✅ Bot integration: All tests passed")
    
    except ImportError:
        print("⚠️ Bot integration: Skipped (bot dependencies not available)")
    
    print()

# ===== LLM VALIDATION TESTS =====

def clean_response_for_irc(response: str) -> str:
    """Clean LLM response for IRC compatibility"""
    import re
    response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
    response = response.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')
    response = re.sub(r'\s+', ' ', response)
    return response.strip()

def is_response_too_long_or_complex(response: str) -> bool:
    """Check if response is too long or complex for IRC"""
    if not response or len(response.strip()) == 0:
        return True
    
    sentences = response.count('.') + response.count('!') + response.count('?')
    if sentences > 2:
        return True
    
    if len(response) > 300:
        return True
    
    complexity_indicators = ['however', 'furthermore', 'moreover', 'nevertheless', 'specifically', 'particularly']
    if any(indicator in response.lower() for indicator in complexity_indicators):
        return True
    
    return False

def test_llm_validation():
    """Test LLM response validation and cleaning"""
    print("🧠 Testing LLM Response Validation...")
    
    # Test response cleaning
    dirty_response = "<think>Let me think</think>This is a test\nwith newlines\r\nand  multiple   spaces."
    clean = clean_response_for_irc(dirty_response)
    expected = "This is a test with newlines and multiple spaces."
    assert clean == expected, f"Expected '{expected}', got '{clean}'"
    
    # Test complexity detection
    simple_response = "Python is a programming language."
    complex_response = "Python is a programming language. However, it has many features. Furthermore, it's used in many domains."
    long_response = "A" * 400
    
    assert is_response_too_long_or_complex(simple_response) == False
    assert is_response_too_long_or_complex(complex_response) == True
    assert is_response_too_long_or_complex(long_response) == True
    assert is_response_too_long_or_complex("") == True
    
    print("✅ LLM validation: All tests passed")
    print()

# ===== THINKING MESSAGE DUPLICATION TESTS =====

def test_thinking_message_duplication():
    """Test that thinking messages are not duplicated"""
    print("🤔 Testing Thinking Message Duplication...")
    
    from unittest.mock import Mock
    
    # Create bot instance
    bot = AircBot()
    
    # Mock connection
    mock_connection = Mock()
    mock_connection.privmsg = Mock()
    
    # Test 1: Normal ask command should show thinking message
    mock_connection.privmsg.reset_mock()
    bot.handle_ask_command(mock_connection, "#test", "user1", "test question")
    
    thinking_calls = [call for call in mock_connection.privmsg.call_args_list 
                     if len(call[0]) > 1 and "🤔" in str(call[0][1])]
    
    if len(thinking_calls) != 1:
        print(f"❌ Expected 1 thinking message, got {len(thinking_calls)}")
        return False
    
    # Test 2: Ask command with show_thinking=False should not show thinking message
    mock_connection.privmsg.reset_mock()
    bot.handle_ask_command(mock_connection, "#test", "user1", "test question", show_thinking=False)
    
    thinking_calls = [call for call in mock_connection.privmsg.call_args_list 
                     if len(call[0]) > 1 and "🤔" in str(call[0][1])]
    
    if len(thinking_calls) != 0:
        print(f"❌ Expected 0 thinking messages, got {len(thinking_calls)}")
        return False
    
    print("✅ Thinking message duplication: All tests passed")
    return True

# ===== COMPREHENSIVE FLOW TESTS =====

def test_complete_flow():
    """Test complete mention + link request flow"""
    print("🔄 Testing Complete Flow...")
    
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
    
    def determine_action(message: str) -> str:
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
    
    passed = 0
    for message, should_be_links, expected_action in test_cases:
        is_mentioned = is_bot_mentioned(message)
        
        if is_mentioned:
            clean_message = message
            for pattern in ["bubba", "aircbot", "bot"]:
                clean_message = clean_message.replace(pattern, "").replace(pattern.title(), "")
            clean_message = clean_message.strip(" ,:;!?").lower()
            
            is_asking_links = is_asking_for_links(clean_message)
            
            if is_asking_links == should_be_links:
                if is_asking_links:
                    action = determine_action(clean_message)
                    if action == expected_action:
                        passed += 1
                    else:
                        print(f"❌ '{message}' -> {action} (expected {expected_action})")
                else:
                    passed += 1
            else:
                print(f"❌ '{message}' -> links={is_asking_links} (expected {should_be_links})")
    
    print(f"✅ Complete flow: {passed}/{len(test_cases)} tests passed")
    print()

# ===== MAIN EXECUTION =====

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='AircBot Test Suite')
    parser.add_argument('--test', choices=['mentions', 'links', 'rate', 'bot', 'llm', 'flow', 'all'], 
                       default='all', help='Which test to run')
    
    args = parser.parse_args()
    
    if args.test == 'all':
        run_all_tests()
    elif args.test == 'mentions':
        test_mention_detection()
    elif args.test == 'links':
        test_link_request_detection()
    elif args.test == 'rate':
        test_rate_limiter()
    elif args.test == 'bot':
        test_bot_integration()
    elif args.test == 'llm':
        test_llm_validation()
    elif args.test == 'flow':
        test_complete_flow()
    elif args.test == 'thinking':
        test_thinking_message_duplication()
