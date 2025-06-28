#!/usr/bin/env python3
"""
Test script for private messaging functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config

def test_private_messaging_config():
    """Test that private messaging configuration is working"""
    print("🧪 Testing Private Messaging Configuration")
    print("=" * 50)
    
    config = Config()
    
    print(f"Private messaging enabled: {config.PRIVATE_MSG_ENABLED}")
    print(f"Links use private messaging: {config.LINKS_USE_PRIVATE_MSG}")
    
    # Test the logic for determining private messaging
    print("\n📋 Private Messaging Logic:")
    print("1. Link commands (when LINKS_USE_PRIVATE_MSG=true):")
    print("   • Detailed results sent to user privately")
    print("   • Channel gets notification: '📩 Sent link information to <user> via private message.'")
    print("   • Keeps channel clean while providing full information")
    
    print("\n2. Direct messages to bot (when PRIVATE_MSG_ENABLED=true):")
    print("   • Commands work normally in private")
    print("   • Regular messages become AI conversations")
    print("   • Rate limiting still applies")
    
    print("\n3. Configuration options:")
    print(f"   • PRIVATE_MSG_ENABLED={config.PRIVATE_MSG_ENABLED}")
    print(f"   • LINKS_USE_PRIVATE_MSG={config.LINKS_USE_PRIVATE_MSG}")
    
    print("\n💡 Usage Examples:")
    print("Channel: !links → User gets private message with results")
    print("Channel: !links stats → User gets private stats message") 
    print("Private: !links → User gets results directly")
    print("Private: How do I debug Python? → AI conversation")
    
    print("\n✅ Private messaging configuration test completed!")

if __name__ == "__main__":
    test_private_messaging_config()
