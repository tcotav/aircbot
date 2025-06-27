#!/usr/bin/env python3
"""
Test script to demonstrate AircBot functionality without connecting to IRC
"""

from database import Database
from link_handler import LinkHandler
import os

def test_bot_functionality():
    """Test the core functionality of the bot"""
    print("🤖 Testing AircBot functionality...\n")
    
    # Initialize components
    db = Database('test_demo.db')
    link_handler = LinkHandler()
    
    # Test messages with links
    test_messages = [
        ("alice", "#friends", "Hey check out this cool project: https://github.com/python/cpython"),
        ("bob", "#friends", "Found this interesting article: https://www.python.org/doc/"),
        ("charlie", "#friends", "Look at this: https://docs.python.org/3/ and also https://pypi.org/"),
        ("alice", "#friends", "That GitHub link again: https://github.com/python/cpython"),  # duplicate
        ("dave", "#friends", "Just chatting, no links here!"),
    ]
    
    print("📨 Processing test messages:")
    for user, channel, message in test_messages:
        print(f"[{channel}] <{user}> {message}")
        
        # Save message
        db.save_message(user, channel, message)
        
        # Extract links
        urls = link_handler.extract_urls(message)
        
        if urls:
            print(f"   🔗 Found {len(urls)} link(s)")
            for url in urls:
                # Get metadata (simplified for demo)
                title, description = link_handler.get_link_metadata(url)
                
                # Save link
                saved = db.save_link(url, title, description, user, channel)
                
                if saved:
                    print(f"   ✅ Saved: {title}")
                else:
                    print(f"   ℹ️  Already exists: {title}")
        else:
            print("   💬 No links found")
        print()
    
    # Test commands
    print("🔍 Testing bot commands:\n")
    
    # Recent links
    print("Command: !links")
    recent = db.get_recent_links("#friends", 5)
    print("📚 Recent links:")
    for link in recent:
        print(f"• {link['title']} (by {link['user']}) - {link['url']}")
    print()
    
    # Detailed links with timestamps
    print("Command: !links details")
    detailed = db.get_links_with_details("#friends", 3)
    print("📚 Recent links (with details):")
    for link in detailed:
        print(f"• {link['title']} | 👤 {link['user']} | 🕐 {link['formatted_time']} | 🔗 {link['url']}")
    print()
    
    # Links by user
    print("Command: !links by charlie")
    user_links = db.get_all_links_by_user("#friends", "charlie")
    print("🔍 Links shared by charlie:")
    for link in user_links:
        print(f"• {link['title']} | 🕐 {link['formatted_time']} | 🔗 {link['url']}")
    print()
    
    # Search
    print("Command: !links search github")
    search_results = db.search_links("#friends", "github", 3)
    print("🔍 Search results for 'github':")
    for link in search_results:
        print(f"• {link['title']} (by {link['user']}) - {link['url']}")
    print()
    
    # Stats
    print("Command: !links stats")
    stats = db.get_link_stats("#friends")
    print(f"📊 Stats: {stats.get('total_links', 0)} links saved by {stats.get('unique_users', 0)} users")
    if 'top_contributor' in stats:
        print(f"   Top contributor: {stats['top_contributor']} with {stats['top_contributor_count']} links")
    print()
    
    # Cleanup
    os.remove('test_demo.db')
    print("✅ Demo completed successfully!")
    print("\nTo run the actual bot:")
    print("1. Edit .env with your IRC server details")
    print("2. Run: ./start.sh")

if __name__ == "__main__":
    test_bot_functionality()
