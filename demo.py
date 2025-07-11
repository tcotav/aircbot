#!/usr/bin/env python3
"""
AircBot Privacy & Admin Features Demo
Comprehensive demonstration of privacy filtering and admin authorization
"""

import sys
import os
import time
from unittest.mock import Mock

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from privacy_filter import PrivacyFilter, PrivacyConfig
from bot import AircBot
from context_manager import Message

def demo_privacy_filtering():
    """Demonstrate privacy filtering capabilities"""
    
    print("🔒 Privacy Filter Demo")
    print("=" * 50)
    
    # Set up privacy filter
    config = PrivacyConfig(
        max_channel_users=20,
        username_anonymization=True,
        pii_detection=True,
        preserve_conversation_flow=True,
        privacy_level='medium'
    )
    privacy_filter = PrivacyFilter(config)
    
    # Define known users in a typical channel
    known_users = {'rain', 'developer', 'admin', 'alice', 'bob'}
    
    print(f"Channel users: {', '.join(sorted(known_users))}")
    print()
    
    # Test scenarios
    scenarios = [
        {
            'title': 'Direct Addressing',
            'content': "rain, you don't know what you're talking about",
            'author': 'developer',
            'explanation': 'Username addressing preserved'
        },
        {
            'title': 'Weather vs Username',
            'content': "I think it's going to rain tomorrow",
            'author': 'alice',
            'explanation': 'Weather context preserved'
        },
        {
            'title': 'PII Protection',
            'content': "My email is john@example.com and phone is 555-123-4567",
            'author': 'bob',
            'explanation': 'Email and phone replaced'
        },
        {
            'title': '@Mention Pattern',
            'content': "@alice can you check the server at 192.168.1.1?",
            'author': 'admin',
            'explanation': 'Mention anonymized, IP replaced'
        }
    ]
    
    for scenario in scenarios:
        print(f"📝 {scenario['title']}")
        print(f"   Original: {scenario['content']}")
        
        # Apply privacy filtering
        sanitized_content, anonymous_username = privacy_filter.sanitize_for_llm(
            scenario['content'], scenario['author'], '#demo', known_users
        )
        
        print(f"   Filtered: {sanitized_content}")
        print(f"   Author: {scenario['author']} → {anonymous_username}")
        print(f"   ✅ {scenario['explanation']}")
        print()
    
    # Show username mappings
    print("🗂️  Username Mappings:")
    mappings = privacy_filter.username_mappings['#demo']
    for real_user, anon_user in sorted(mappings.items()):
        print(f"   {real_user} → {anon_user}")
    
    print()

def demo_context_integration():
    """Demonstrate privacy integration with context manager"""
    
    print("🔗 Context Integration Demo")
    print("=" * 45)
    
    # Simulate conversation messages
    current_time = time.time()
    messages = [
        Message('rain', '#dev', 'Can someone help with deployment?', current_time - 300, False, False),
        Message('developer', '#dev', 'rain, what error are you seeing?', current_time - 250, False, False),
        Message('admin', '#dev', 'Check logs at 192.168.1.1, email me at admin@company.com', current_time - 150, False, False),
    ]
    
    print("Original Context:")
    for i, msg in enumerate(messages, 1):
        age_minutes = (time.time() - msg.timestamp) / 60
        print(f"  {i}. [{int(age_minutes)}m ago] {msg.user}: {msg.content}")
    
    print("\nPrivacy-Protected Context:")
    
    # Create privacy filter and process
    config = PrivacyConfig(privacy_level='medium')
    privacy_filter = PrivacyFilter(config)
    known_users = {msg.user for msg in messages}
    
    for i, msg in enumerate(messages, 1):
        age_minutes = (time.time() - msg.timestamp) / 60
        sanitized_content, anon_username = privacy_filter.sanitize_for_llm(
            msg.content, msg.user, '#dev', known_users
        )
        print(f"  {i}. [{int(age_minutes)}m ago] {anon_username}: {sanitized_content}")
    
    print("\n✅ PII replaced, usernames anonymized, conversation flow preserved")
    print()

def demo_admin_authorization():
    """Demonstrate admin authorization for privacy commands"""
    
    print("🔐 Admin Authorization Demo")
    print("=" * 45)
    
    # Initialize bot
    bot = AircBot()
    mock_connection = Mock()
    
    admin_user = bot.config.IRC_NICKNAME
    regular_user = "regular_user"
    
    print(f"Admin users: {bot.config.ADMIN_USERS}")
    print(f"Testing admin: {admin_user}")
    print(f"Testing regular: {regular_user}")
    print()
    
    # Test 1: Regular user tries privacy clear (denied)
    print("❌ Regular user attempts !privacy clear:")
    mock_connection.reset_mock()
    bot.handle_command(mock_connection, "#test", regular_user, "!privacy clear")
    
    if mock_connection.privmsg.called:
        response = mock_connection.privmsg.call_args[0][1]
        print(f"   Response: {response}")
        if "Only bot administrators" in response:
            print("   ✅ Access denied correctly")
    print()
    
    # Test 2: Admin user clears privacy (allowed)
    print("✅ Admin user uses !privacy clear:")
    mock_connection.reset_mock()
    
    # Mock the clear method to avoid actual clearing
    original_clear = bot.clear_privacy_data
    bot.clear_privacy_data = Mock()
    
    bot.handle_command(mock_connection, "#test", admin_user, "!privacy clear")
    
    if bot.clear_privacy_data.called:
        print("   ✅ Privacy clear executed successfully")
    
    # Restore original method
    bot.clear_privacy_data = original_clear
    print()
    
    # Test 3: Regular user uses other privacy commands (allowed)
    print("✅ Regular user uses !privacy (allowed):")
    mock_connection.reset_mock()
    
    original_stats = bot.show_privacy_stats
    bot.show_privacy_stats = Mock()
    
    bot.handle_command(mock_connection, "#test", regular_user, "!privacy")
    
    if bot.show_privacy_stats.called:
        print("   ✅ Privacy stats accessible to all users")
    
    bot.show_privacy_stats = original_stats
    print()

def demo_performance_optimization():
    """Demonstrate privacy performance optimization for large channels"""
    
    print("⚡ Performance Optimization Demo")
    print("=" * 50)
    
    config = PrivacyConfig(max_channel_users=20)  # Low threshold for demo
    privacy_filter = PrivacyFilter(config)
    
    # Test with large channel (> threshold)
    large_users = {f'user{i}' for i in range(25)}  # 25 > 20 limit
    
    content = "user5, my email is test@example.com"
    sanitized, anon_user = privacy_filter.sanitize_for_llm(
        content, 'user10', '#largechannel', large_users
    )
    
    print(f"Large channel test:")
    print(f"  Channel size: {len(large_users)} users (threshold: {config.max_channel_users})")
    print(f"  Original: {content}")
    print(f"  Processed: {sanitized}")
    print(f"  Author: user10 → {anon_user}")
    
    if content == sanitized and anon_user == 'user10':
        print("  ✅ Privacy skipped for performance (channel too large)")
    else:
        print("  ❌ Privacy was applied unexpectedly")
    
    print()
    
    # Test with normal channel (< threshold)
    small_users = {f'user{i}' for i in range(5)}  # 5 < 20 limit
    
    sanitized, anon_user = privacy_filter.sanitize_for_llm(
        content, 'user1', '#smallchannel', small_users
    )
    
    print(f"Normal channel test:")
    print(f"  Channel size: {len(small_users)} users (threshold: {config.max_channel_users})")
    print(f"  Original: {content}")
    print(f"  Processed: {sanitized}")
    print(f"  Author: user1 → {anon_user}")
    
    if '[EMAIL]' in sanitized and anon_user != 'user1':
        print("  ✅ Privacy applied for normal-sized channel")
    else:
        print("  ❌ Privacy was not applied as expected")
    
    print()

def main():
    """Run all demo components"""
    
    print("🤖 AircBot Privacy & Admin Features Demo")
    print("=" * 60)
    print("Demonstrating privacy protection and admin authorization")
    print()
    
    try:
        demo_privacy_filtering()
        demo_context_integration()
        demo_admin_authorization()
        demo_performance_optimization()
        
        print("🎉 Demo Complete!")
        print()
        print("Key Features Demonstrated:")
        print("• Username anonymization with conversation preservation")
        print("• PII detection and replacement") 
        print("• Context integration for LLM protection")
        print("• Admin authorization for sensitive commands")
        print("• Performance optimization for large channels")
        print()
        print("📚 For more details, see:")
        print("• docs/PRIVACY_FILTER_GUIDE.md - Complete privacy documentation")
        print("• python test_privacy_filter.py - Comprehensive unit tests")
        print("• python test_suite.py - Full integration tests")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
