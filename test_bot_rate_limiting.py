#!/usr/bin/env python3
"""
Test bot rate limiting integration
"""

import sys
import os
import time

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock IRC connection and event for testing
class MockConnection:
    def __init__(self):
        self.messages = []
        self.nickname = "bubba"
    
    def privmsg(self, channel, message):
        self.messages.append(f"[{channel}] {message}")
        print(f"Bot says: {message}")
    
    def get_nickname(self):
        return self.nickname

class MockEvent:
    def __init__(self, nick, message):
        self.source = MockSource(nick)
        self.target = "#test"
        self.arguments = [message]

class MockSource:
    def __init__(self, nick):
        self.nick = nick

def test_bot_rate_limiting():
    """Test that the bot correctly applies rate limiting"""
    
    print("🤖 Testing Bot Rate Limiting Integration...\n")
    
    # Import after setting up mocks
    from bot import AircBot
    
    # Create bot instance
    bot = AircBot()
    
    # Override rate limits for testing
    bot.rate_limiter = bot.rate_limiter.__class__(user_limit_per_minute=2, total_limit_per_minute=5)
    
    # Mock connection
    connection = MockConnection()
    channel = "#test"
    
    print("Configuration:")
    print(f"• User limit: 2 per minute")
    print(f"• Total limit: 5 per minute")
    print()
    
    # Test command rate limiting
    print("1. Testing command rate limiting...")
    
    # First command should work
    print("Alice sends: !help")
    bot.handle_command(connection, channel, "alice", "!help")
    print()
    
    # Second command should work
    print("Alice sends: !links")
    bot.handle_command(connection, channel, "alice", "!links")
    print()
    
    # Third command should be rate limited
    print("Alice sends: !ask test")
    bot.handle_command(connection, channel, "alice", "!ask test")
    print()
    
    # Different user should still work
    print("Bob sends: !help")
    bot.handle_command(connection, channel, "bob", "!help")
    print()
    
    # Test mention rate limiting
    print("2. Testing mention rate limiting...")
    
    # Charlie's first mention should work
    print("Charlie says: bubba what links do you have?")
    bot.handle_name_mention(connection, channel, "charlie", "bubba what links do you have?")
    print()
    
    # Charlie's second mention should work
    print("Charlie says: aircbot tell me a joke")
    bot.handle_name_mention(connection, channel, "charlie", "aircbot tell me a joke")
    print()
    
    # Charlie's third mention should be rate limited
    print("Charlie says: bot show me links")
    bot.handle_name_mention(connection, channel, "charlie", "bot show me links")
    print()
    
    # Test rate limit stats command
    print("3. Testing rate limit stats...")
    print("Alice sends: !ratelimit")
    bot.handle_command(connection, channel, "alice", "!ratelimit")  # This should be blocked
    print()
    
    print("Diana sends: !rl")
    bot.handle_command(connection, channel, "diana", "!rl")  # This should work
    print()

def test_rate_limit_recovery():
    """Test that rate limits reset over time"""
    
    print("\n⏰ Testing Rate Limit Recovery...\n")
    
    from rate_limiter import RateLimiter
    
    # Create limiter with 1-second window for quick testing
    limiter = RateLimiter(user_limit_per_minute=1, total_limit_per_minute=3)
    limiter.window_size = 2  # 2 seconds for quick testing
    
    print("Using 2-second window for quick testing...")
    
    # User hits limit
    assert limiter.is_allowed('test_user') == True
    print("✅ Request 1: allowed")
    
    assert limiter.is_allowed('test_user') == False
    print("✅ Request 2: blocked (limit reached)")
    
    # Wait for window to reset
    print("Waiting 3 seconds for rate limit to reset...")
    time.sleep(3)
    
    # Should be allowed again
    assert limiter.is_allowed('test_user') == True
    print("✅ Request after reset: allowed")
    
    print("✅ Rate limit recovery works correctly")

if __name__ == "__main__":
    test_bot_rate_limiting()
    test_rate_limit_recovery()
    print("\n🎉 All bot rate limiting tests completed!")
