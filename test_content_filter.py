#!/usr/bin/env python3
"""
Quick test of the content filter functionality
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from content_filter import ContentFilter

def test_content_filter():
    """Test the content filter with various inputs"""
    
    # Mock config for testing
    class MockConfig:
        DATABASE_PATH = "data/links.db"
    
    config = MockConfig()
    content_filter = ContentFilter(config)
    
    # Test cases
    test_cases = [
        # (message, expected_allowed, description)
        ("Hello world", True, "Normal message"),
        ("Can you help me with Python?", True, "Technical question"),
        ("What's the weather like?", True, "Casual question"),
        ("This is fucking ridiculous", False, "Profanity"),
        ("I want to hack into this system", False, "Hacking reference"),
        ("My SSN is 123-45-6789", False, "Social Security Number"),
        ("Call me at 555-123-4567", False, "Phone number"),
        ("HELLO THIS IS ALL CAPS!!!!!", False, "Excessive caps and punctuation"),
        ("a" * 1001, False, "Message too long"),
        ("Normal conversation about coding", True, "Programming discussion"),
    ]
    
    print("🛡️ Testing Content Filter")
    print("=" * 40)
    
    passed = 0
    failed = 0
    
    for message, expected_allowed, description in test_cases:
        result = content_filter.filter_content(message, "testuser", "#testchannel")
        
        if result.is_allowed == expected_allowed:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
            
        print(f"{status} - {description}")
        print(f"   Message: {message[:50]}{'...' if len(message) > 50 else ''}")
        print(f"   Expected: {'Allowed' if expected_allowed else 'Blocked'}")
        print(f"   Got: {'Allowed' if result.is_allowed else 'Blocked'}")
        if not result.is_allowed:
            print(f"   Reason: {result.reason}")
        print()
    
    print(f"Results: {passed} passed, {failed} failed")
    
    # Test audit stats
    print("\n📊 Testing Audit Stats")
    stats = content_filter.get_audit_stats(24)
    print(f"Blocked attempts: {stats['total_blocked']}")
    print(f"Filter types: {stats['by_filter_type']}")
    
    return failed == 0

if __name__ == "__main__":
    success = test_content_filter()
    sys.exit(0 if success else 1)
