#!/usr/bin/env python3
"""
Comprehensive tests for privacy filter functionality
Tests username anonymization, PII detection, and conversation flow preservation
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from privacy_filter import PrivacyFilter, PrivacyConfig
from context_manager import ContextManager, Message
import time

class TestPrivacyFilter(unittest.TestCase):
    """Test privacy filter functionality"""
    
    def setUp(self):
        """Set up test privacy filter"""
        self.config = PrivacyConfig(
            max_channel_users=20,
            username_anonymization=True,
            pii_detection=True,
            preserve_conversation_flow=True,
            privacy_level='medium'
        )
        self.privacy_filter = PrivacyFilter(self.config)
    
    def test_username_anonymization_basic(self):
        """Test basic username anonymization"""
        known_users = {'alice', 'bob', 'charlie'}
        
        # Test simple message
        content = "alice is working on this"
        sanitized, anon_user = self.privacy_filter.sanitize_for_llm(
            content, 'bob', '#test', known_users
        )
        
        # Should anonymize alice, and bob should get anonymous username
        self.assertIn('User', sanitized)
        self.assertNotIn('alice', sanitized)
        self.assertIn('User', anon_user)
        self.assertNotEqual(anon_user, 'bob')
    
    def test_addressing_pattern_detection(self):
        """Test detection of direct addressing patterns"""
        known_users = {'rain', 'developer', 'admin'}
        
        # Test direct addressing with comma
        content = "rain, you don't know what you're talking about"
        sanitized, _ = self.privacy_filter.sanitize_for_llm(
            content, 'developer', '#test', known_users
        )
        
        # Should replace 'rain,' with anonymous username
        self.assertNotIn('rain,', sanitized)
        self.assertIn('User', sanitized)
        self.assertIn("you don't know", sanitized)  # Rest should be preserved
    
    def test_common_word_protection(self):
        """Test protection of common word usernames in context"""
        known_users = {'rain', 'weather_guy'}
        
        # Weather discussion - should NOT replace 'rain'
        content = "I think it's going to rain tomorrow"
        sanitized, _ = self.privacy_filter.sanitize_for_llm(
            content, 'weather_guy', '#general', known_users
        )
        
        # 'rain' should NOT be replaced (it's about weather, not the user)
        self.assertIn('rain', sanitized)
        
        # But direct addressing should be replaced
        content2 = "rain, what do you think about the weather?"
        sanitized2, _ = self.privacy_filter.sanitize_for_llm(
            content2, 'weather_guy', '#general', known_users
        )
        
        # 'rain,' should be replaced (direct addressing)
        self.assertNotIn('rain,', sanitized2)
        self.assertIn('User', sanitized2)
    
    def test_pii_detection(self):
        """Test PII detection and replacement"""
        known_users = {'alice'}
        
        test_cases = [
            ("My email is john@example.com", "[EMAIL]"),
            ("Call me at 555-123-4567", "[PHONE]"),
            ("My SSN is 123-45-6789", "[SSN]"),
            ("Card number: 1234 5678 9012 3456", "[CREDIT_CARD]"),
            ("Server IP: 192.168.1.1", "[IP_ADDRESS]"),
            ("Check my GitHub: https://github.com/username", "[URL_WITH_USER]")
        ]
        
        for original, expected_pattern in test_cases:
            sanitized, _ = self.privacy_filter.sanitize_for_llm(
                original, 'alice', '#test', known_users
            )
            self.assertIn(expected_pattern, sanitized, 
                         f"Expected {expected_pattern} in sanitized version of: {original}")
    
    def test_channel_size_limit(self):
        """Test privacy bypass for large channels"""
        # Create large set of users (more than limit)
        large_users = {f'user{i}' for i in range(25)}  # 25 > 20 limit
        
        content = "user5, can you help me with this?"
        sanitized, anon_user = self.privacy_filter.sanitize_for_llm(
            content, 'user10', '#largechannel', large_users
        )
        
        # Privacy should be skipped due to channel size
        self.assertEqual(content, sanitized)  # No changes
        self.assertEqual(anon_user, 'user10')  # Original username
    
    def test_privacy_level_none(self):
        """Test privacy level 'none' bypasses all filtering"""
        config = PrivacyConfig(privacy_level='none')
        filter_none = PrivacyFilter(config)
        
        known_users = {'alice', 'bob'}
        content = "alice, my email is test@example.com"
        
        sanitized, anon_user = filter_none.sanitize_for_llm(
            content, 'bob', '#test', known_users
        )
        
        # Nothing should be changed
        self.assertEqual(content, sanitized)
        self.assertEqual(anon_user, 'bob')
    
    def test_consistent_username_mapping(self):
        """Test that username mappings are consistent across calls"""
        known_users = {'alice', 'bob'}
        
        # First call
        _, anon1 = self.privacy_filter.sanitize_for_llm(
            "hello", 'alice', '#test', known_users
        )
        
        # Second call with same user
        _, anon2 = self.privacy_filter.sanitize_for_llm(
            "goodbye", 'alice', '#test', known_users
        )
        
        # Should get same anonymous username
        self.assertEqual(anon1, anon2)
    
    def test_mention_pattern_detection(self):
        """Test @mention pattern detection"""
        known_users = {'alice', 'bob'}
        
        content = "@alice can you look at this?"
        sanitized, _ = self.privacy_filter.sanitize_for_llm(
            content, 'bob', '#test', known_users
        )
        
        # Should replace @alice with anonymous username
        self.assertNotIn('@alice', sanitized)
        self.assertIn('User', sanitized)
    
    def test_privacy_stats(self):
        """Test privacy statistics tracking"""
        known_users = {'alice', 'bob', 'charlie'}
        
        # Add some users to channel
        for user in known_users:
            self.privacy_filter.update_channel_users('#test', user)
        
        stats = self.privacy_filter.get_privacy_stats('#test')
        
        self.assertEqual(stats['active_users'], 3)
        self.assertEqual(stats['privacy_level'], 'medium')
        self.assertTrue(stats['privacy_applied'])  # 3 users < 20 limit
    
    def test_clear_channel_data(self):
        """Test clearing privacy data for a channel"""
        known_users = {'alice', 'bob'}
        
        # Generate some mappings
        self.privacy_filter.sanitize_for_llm("test", 'alice', '#test', known_users)
        
        # Verify data exists
        self.assertIn('#test', self.privacy_filter.username_mappings)
        
        # Clear data
        self.privacy_filter.clear_channel_data('#test')
        
        # Verify data cleared
        self.assertNotIn('#test', self.privacy_filter.username_mappings)

class TestContextManagerPrivacyIntegration(unittest.TestCase):
    """Test privacy filter integration with context manager"""
    
    def setUp(self):
        """Set up mock config and context manager"""
        # Mock config with privacy enabled
        self.mock_config = Mock()
        self.mock_config.MESSAGE_QUEUE_SIZE = 50
        self.mock_config.CONTEXT_ANALYSIS_ENABLED = True
        self.mock_config.CONTEXT_RELEVANCE_THRESHOLD = 0.3
        self.mock_config.MAX_CONTEXT_MESSAGES = 10
        self.mock_config.PRIVACY_FILTER_ENABLED = True
        self.mock_config.PRIVACY_MAX_CHANNEL_USERS = 20
        self.mock_config.PRIVACY_USERNAME_ANONYMIZATION = True
        self.mock_config.PRIVACY_PII_DETECTION = True
        self.mock_config.PRIVACY_PRESERVE_CONVERSATION_FLOW = True
        self.mock_config.PRIVACY_LEVEL = 'medium'
        
        # Add required weight configs
        self.mock_config.WEIGHT_KEYWORD_OVERLAP = 0.4
        self.mock_config.WEIGHT_TECHNICAL_KEYWORDS = 0.3
        self.mock_config.WEIGHT_QUESTION_CONTEXT = 0.15
        self.mock_config.WEIGHT_RECENCY_BONUS = 0.1
        self.mock_config.WEIGHT_BOT_INTERACTION = 0.1
        self.mock_config.WEIGHT_URL_BONUS = 0.2
        self.mock_config.PENALTY_SHORT_MESSAGE = 0.7
        
        self.context_manager = ContextManager(self.mock_config)
    
    def test_privacy_integration_enabled(self):
        """Test that privacy filter is properly integrated"""
        self.assertIsNotNone(self.context_manager.privacy_filter)
        self.assertTrue(hasattr(self.context_manager, 'get_privacy_stats'))
    
    def test_format_context_with_privacy(self):
        """Test context formatting with privacy protection"""
        # Add some messages
        current_time = time.time()
        messages = [
            Message('alice', '#test', 'alice, can you help?', current_time - 300, False, False),
            Message('bob', '#test', 'My email is bob@example.com', current_time - 200, False, False),
            Message('charlie', '#test', 'Sure, what do you need?', current_time - 100, False, False)
        ]
        
        # Format with privacy
        formatted = self.context_manager.format_context_for_llm(messages)
        
        # Should contain privacy-protected content
        self.assertIn('Recent conversation context:', formatted)
        self.assertNotIn('alice', formatted)  # Usernames should be anonymized
        self.assertNotIn('bob@example.com', formatted)  # PII should be replaced
        self.assertIn('[EMAIL]', formatted)  # PII replacement
        self.assertIn('User', formatted)  # Anonymous usernames
    
    def test_get_channel_users(self):
        """Test getting channel users"""
        # Add messages to build up user list
        self.context_manager.add_message('alice', '#test', 'hello', time.time())
        self.context_manager.add_message('bob', '#test', 'hi there', time.time())
        
        users = self.context_manager.get_channel_users('#test')
        self.assertEqual(users, {'alice', 'bob'})
    
    def test_privacy_stats_integration(self):
        """Test privacy statistics through context manager"""
        # Add some users
        self.context_manager.add_message('alice', '#test', 'test1', time.time())
        self.context_manager.add_message('bob', '#test', 'test2', time.time())
        
        stats = self.context_manager.get_privacy_stats('#test')
        
        self.assertTrue(stats['privacy_enabled'])
        self.assertIn('privacy_level', stats)
        self.assertIn('active_users', stats)

class TestPrivacyScenarios(unittest.TestCase):
    """Test real-world privacy scenarios"""
    
    def setUp(self):
        """Set up privacy filter for scenario testing"""
        self.config = PrivacyConfig(
            max_channel_users=20,
            username_anonymization=True,
            pii_detection=True,
            preserve_conversation_flow=True,
            privacy_level='medium'
        )
        self.privacy_filter = PrivacyFilter(self.config)
    
    def test_tech_support_scenario(self):
        """Test typical tech support conversation"""
        known_users = {'rain', 'developer', 'admin', 'newbie'}
        
        scenarios = [
            # Direct addressing with common word username
            ("rain, you don't know how to fix this", "User1, you don't know how to fix this"),
            
            # Weather discussion (should not replace 'rain')
            ("I hope it doesn't rain during the deployment", "I hope it doesn't rain during the deployment"),
            
            # Technical discussion with username references
            ("developer mentioned that rain said it's a bug", "User2 mentioned that User1 said it's a bug"),
            
            # PII in support request
            ("My server IP is 192.168.1.1 and email is admin@company.com", 
             "My server IP is [IP_ADDRESS] and email is [EMAIL]"),
            
            # Mixed scenario
            ("@rain, can you check the logs at https://github.com/mycompany/repo?", 
             "User1, can you check the logs at [URL_WITH_USER]?")
        ]
        
        for original, expected_pattern in scenarios:
            sanitized, _ = self.privacy_filter.sanitize_for_llm(
                original, 'tester', '#support', known_users
            )
            
            # Check key parts of expected transformation
            if "User1" in expected_pattern:
                self.assertIn("User1", sanitized, f"Failed for: {original}")
            if "[IP_ADDRESS]" in expected_pattern:
                self.assertIn("[IP_ADDRESS]", sanitized, f"Failed for: {original}")
            if "[EMAIL]" in expected_pattern:
                self.assertIn("[EMAIL]", sanitized, f"Failed for: {original}")
            if "rain during the deployment" in expected_pattern:
                self.assertIn("rain during the deployment", sanitized, f"Failed for: {original}")
    
    def test_large_channel_performance(self):
        """Test performance consideration for large channels"""
        # Simulate large channel
        large_users = {f'user{i}' for i in range(50)}  # 50 users > 20 limit
        
        start_time = time.time()
        
        # Should skip privacy filtering quickly
        content = "user10, can you help with this complex issue?"
        sanitized, anon_user = self.privacy_filter.sanitize_for_llm(
            content, 'user5', '#largechannel', large_users
        )
        
        end_time = time.time()
        
        # Should be very fast (no processing)
        self.assertLess(end_time - start_time, 0.1)  # Less than 100ms
        
        # Content should be unchanged
        self.assertEqual(content, sanitized)
        self.assertEqual(anon_user, 'user5')

def run_privacy_tests():
    """Run all privacy filter tests"""
    print("🔒 Running Privacy Filter Tests...")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPrivacyFilter))
    suite.addTests(loader.loadTestsFromTestCase(TestContextManagerPrivacyIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPrivacyScenarios))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\n{'✅ All tests passed!' if success else '❌ Some tests failed!'}")
    
    return success

if __name__ == "__main__":
    success = run_privacy_tests()
    sys.exit(0 if success else 1)
