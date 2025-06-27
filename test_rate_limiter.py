#!/usr/bin/env python3
"""
Test rate limiting functionality
"""

import time
import sys
import os

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rate_limiter import RateLimiter

def test_rate_limiter():
    """Test the rate limiter functionality"""
    
    print("🧪 Testing Rate Limiter...\n")
    
    # Create a rate limiter with low limits for testing
    limiter = RateLimiter(user_limit_per_minute=2, total_limit_per_minute=5)
    
    print("Configuration:")
    print(f"• User limit: 2 per minute")
    print(f"• Total limit: 5 per minute")
    print()
    
    # Test user rate limiting
    print("1. Testing user rate limiting...")
    
    # User 'alice' should be allowed 2 requests
    assert limiter.is_allowed('alice') == True, "First request should be allowed"
    print("✅ alice: request 1 allowed")
    
    assert limiter.is_allowed('alice') == True, "Second request should be allowed"
    print("✅ alice: request 2 allowed")
    
    assert limiter.is_allowed('alice') == False, "Third request should be blocked"
    print("✅ alice: request 3 blocked (user limit)")
    
    # Different user should still be allowed
    assert limiter.is_allowed('bob') == True, "Bob's first request should be allowed"
    print("✅ bob: request 1 allowed")
    
    assert limiter.is_allowed('bob') == True, "Bob's second request should be allowed"
    print("✅ bob: request 2 allowed")
    
    assert limiter.is_allowed('bob') == False, "Bob's third request should be blocked"
    print("✅ bob: request 3 blocked (user limit)")
    
    print()
    
    # Test total rate limiting
    print("2. Testing total rate limiting...")
    
    # We've used 4 requests so far (2 alice, 2 bob)
    # One more should be allowed, then blocked
    assert limiter.is_allowed('charlie') == True, "Charlie's first request should be allowed"
    print("✅ charlie: request 1 allowed (total: 5/5)")
    
    assert limiter.is_allowed('diana') == False, "Diana's request should be blocked by total limit"
    print("✅ diana: request blocked (total limit reached)")
    
    print()
    
    # Test stats
    print("3. Testing statistics...")
    stats = limiter.get_stats()
    print(f"✅ Total stats: {stats}")
    
    alice_stats = limiter.get_user_stats('alice')
    print(f"✅ Alice stats: {alice_stats}")
    
    bob_stats = limiter.get_user_stats('bob')
    print(f"✅ Bob stats: {bob_stats}")
    
    print()
    
    # Test time window (quick test with short sleep)
    print("4. Testing time window behavior...")
    print("Waiting 2 seconds to test cleanup...")
    time.sleep(2)
    
    # Stats should still show recent requests
    stats_after = limiter.get_stats()
    print(f"✅ Stats after 2s: {stats_after}")
    
    print()
    print("✅ All rate limiter tests passed!")

def test_rate_limiter_edge_cases():
    """Test edge cases for rate limiter"""
    
    print("\n🔬 Testing Rate Limiter Edge Cases...\n")
    
    # Test with zero limits
    print("1. Testing zero limits...")
    zero_limiter = RateLimiter(user_limit_per_minute=0, total_limit_per_minute=0)
    
    assert zero_limiter.is_allowed('test') == False, "Zero limit should block all requests"
    print("✅ Zero limits work correctly")
    
    # Test with high limits
    print("2. Testing high limits...")
    high_limiter = RateLimiter(user_limit_per_minute=1000, total_limit_per_minute=1000)
    
    for i in range(10):
        assert high_limiter.is_allowed(f'user{i}') == True, f"High limit request {i} should be allowed"
    
    print("✅ High limits work correctly")
    
    # Test same user multiple times
    print("3. Testing rapid requests from same user...")
    rapid_limiter = RateLimiter(user_limit_per_minute=3, total_limit_per_minute=10)
    
    allowed_count = 0
    for i in range(5):
        if rapid_limiter.is_allowed('rapid_user'):
            allowed_count += 1
    
    assert allowed_count == 3, f"Should allow exactly 3 requests, got {allowed_count}"
    print(f"✅ Rapid requests: {allowed_count}/5 allowed (correct)")
    
    print("\n✅ All edge case tests passed!")

if __name__ == "__main__":
    test_rate_limiter()
    test_rate_limiter_edge_cases()
    print("\n🎉 All tests completed successfully!")
