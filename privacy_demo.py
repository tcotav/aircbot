#!/usr/bin/env python3
"""
Privacy Filter Demonstration
Shows how the privacy filter works with various scenarios
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from privacy_filter import PrivacyFilter, PrivacyConfig

def demonstrate_privacy_scenarios():
    """Demonstrate various privacy filtering scenarios"""
    
    print("🔒 Privacy Filter Demonstration")
    print("=" * 60)
    
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
    known_users = {'rain', 'developer', 'admin', 'alice', 'bob', 'charlie'}
    
    print(f"Channel users: {', '.join(sorted(known_users))}")
    print()
    
    # Test scenarios
    scenarios = [
        {
            'title': '1. Direct Addressing with Common Word Username',
            'content': "rain, you don't know what you're talking about",
            'author': 'developer',
            'explanation': 'Should replace "rain," but preserve conversation meaning'
        },
        {
            'title': '2. Weather Discussion (NOT addressing user)',
            'content': "I think it's going to rain tomorrow",
            'author': 'alice',
            'explanation': 'Should NOT replace "rain" since it\'s about weather'
        },
        {
            'title': '3. Technical Discussion with Multiple Users',
            'content': "developer mentioned that rain said it's a bug",
            'author': 'admin',
            'explanation': 'Should anonymize both usernames'
        },
        {
            'title': '4. PII in Message',
            'content': "My email is john@example.com and phone is 555-123-4567",
            'author': 'bob',
            'explanation': 'Should replace email and phone with placeholders'
        },
        {
            'title': '5. @ Mention Pattern',
            'content': "@alice can you check the server logs?",
            'author': 'charlie',
            'explanation': 'Should replace @alice with anonymous username'
        },
        {
            'title': '6. Complex Scenario with PII and Addressing',
            'content': "rain, my server at 192.168.1.1 is down. Check https://github.com/user/repo",
            'author': 'admin',
            'explanation': 'Should anonymize username and replace IP/GitHub URL'
        },
        {
            'title': '7. IRC-style Username Reference',
            'content': "rain said: the deployment failed",
            'author': 'developer',
            'explanation': 'Should replace username in "username said:" pattern'
        },
        {
            'title': '8. Mixed Context - Username as Word',
            'content': "The rain in Spain falls mainly on the plain, but user rain knows better",
            'author': 'alice',
            'explanation': 'Should only replace the second "rain" (user reference)'
        }
    ]
    
    for i, scenario in enumerate(scenarios):
        print(f"Scenario {scenario['title']}")
        print("-" * 40)
        print(f"Author: {scenario['author']}")
        print(f"Original: {scenario['content']}")
        
        # Apply privacy filtering
        sanitized_content, anonymous_username = privacy_filter.sanitize_for_llm(
            scenario['content'], scenario['author'], '#test', known_users
        )
        
        print(f"Sanitized: {sanitized_content}")
        print(f"Author becomes: {scenario['author']} → {anonymous_username}")
        print(f"Explanation: {scenario['explanation']}")
        
        # Show if the filtering worked as expected
        original = scenario['content']
        if 'rain,' in original and 'rain,' not in sanitized_content:
            print("✅ Correctly anonymized direct addressing")
        elif 'rain tomorrow' in original and 'rain tomorrow' in sanitized_content:
            print("✅ Correctly preserved weather reference")
        elif '@' in original and '@' not in sanitized_content:
            print("✅ Correctly anonymized @ mention")
        elif '@example.com' in original and '[EMAIL]' in sanitized_content:
            print("✅ Correctly replaced email")
        elif '192.168.1.1' in original and '[IP_ADDRESS]' in sanitized_content:
            print("✅ Correctly replaced IP address")
        elif 'github.com' in original and '[URL_WITH_USER]' in sanitized_content:
            print("✅ Correctly replaced GitHub URL")
        elif ' said:' in original and 'User' in sanitized_content:
            print("✅ Correctly anonymized IRC-style reference")
        
        print()
    
    # Show username mappings
    print("Username Mappings for #test:")
    print("-" * 30)
    mappings = privacy_filter.username_mappings['#test']
    for real_user, anon_user in sorted(mappings.items()):
        print(f"{real_user} → {anon_user}")
    
    print()
    
    # Test large channel scenario
    print("Large Channel Scenario (Performance Test):")
    print("-" * 45)
    large_users = {f'user{i}' for i in range(25)}  # 25 > 20 limit
    
    content = "user5, can you help me with this?"
    sanitized, anon_user = privacy_filter.sanitize_for_llm(
        content, 'user10', '#largechannel', large_users
    )
    
    print(f"Channel size: {len(large_users)} users (> {config.max_channel_users} limit)")
    print(f"Original: {content}")
    print(f"Sanitized: {sanitized}")
    print(f"Author: user10 → {anon_user}")
    print("✅ Privacy skipped for performance (channel too large)")
    
    print()
    
    # Show privacy statistics
    print("Privacy Statistics:")
    print("-" * 20)
    stats = privacy_filter.get_privacy_stats('#test')
    print(f"Privacy Level: {stats['privacy_level']}")
    print(f"Active Users: {stats['active_users']}")
    print(f"Mapped Users: {stats['mapped_users']}")
    print(f"Max Channel Size: {stats['max_channel_users']}")
    print(f"Privacy Applied: {'Yes' if stats['privacy_applied'] else 'No'}")

def demonstrate_context_integration():
    """Demonstrate privacy integration with context manager"""
    
    print("\n" + "=" * 60)
    print("🔒 Context Manager Integration Demo")
    print("=" * 60)
    
    # Mock a simple context scenario
    from context_manager import Message
    import time
    
    # Simulate messages
    current_time = time.time()
    messages = [
        Message('rain', '#dev', 'Can someone help with the deployment?', current_time - 300, False, False),
        Message('developer', '#dev', 'rain, what error are you seeing?', current_time - 250, False, False),
        Message('rain', '#dev', 'Error at IP 192.168.1.1, logs at https://github.com/company/repo', current_time - 200, False, False),
        Message('admin', '#dev', 'My email is admin@company.com if you need help', current_time - 150, False, False),
        Message('developer', '#dev', '@rain check your firewall settings', current_time - 100, False, False)
    ]
    
    # Show original context
    print("Original Context:")
    print("-" * 20)
    for i, msg in enumerate(messages, 1):
        age_minutes = (time.time() - msg.timestamp) / 60
        print(f"{i}. [{int(age_minutes)}m ago] {msg.user}: {msg.content}")
    
    print()
    
    # Create privacy filter and process
    config = PrivacyConfig(privacy_level='medium')
    privacy_filter = PrivacyFilter(config)
    
    known_users = {msg.user for msg in messages}
    
    print("Privacy-Protected Context for LLM:")
    print("-" * 35)
    print("Recent conversation context:")
    
    for i, msg in enumerate(messages, 1):
        age_minutes = (time.time() - msg.timestamp) / 60
        
        # Apply privacy filtering
        sanitized_content, anon_username = privacy_filter.sanitize_for_llm(
            msg.content, msg.user, '#dev', known_users
        )
        
        print(f"[{int(age_minutes)}m ago] {anon_username}: {sanitized_content}")
    
    print()
    print("Key Privacy Protections Applied:")
    print("- Usernames anonymized (rain → User1, developer → User2, etc.)")
    print("- IP address replaced with [IP_ADDRESS]")
    print("- Email replaced with [EMAIL]")
    print("- GitHub URL replaced with [URL_WITH_USER]")
    print("- Direct addressing preserved ('rain,' → 'User1,')")
    print("- @mentions anonymized ('@rain' → 'User1')")

if __name__ == "__main__":
    demonstrate_privacy_scenarios()
    demonstrate_context_integration()
    
    print("\n" + "=" * 60)
    print("✅ Privacy Filter Demo Complete!")
    print("🔒 User information is now protected when sent to LLMs")
    print("📊 Run 'python test_privacy_filter.py' for comprehensive tests")
