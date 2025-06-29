#!/usr/bin/env python3
"""
Comprehensive test suite for content filter functionality
"""

import sys
import os
import unittest
import sqlite3
import tempfile
import shutil
from unittest.mock import Mock, patch

sys.path.append(os.path.dirname(__file__))

from content_filter import ContentFilter, FilterResult

class TestContentFilter(unittest.TestCase):
    """Comprehensive tests for ContentFilter class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for test database
        self.test_dir = tempfile.mkdtemp()
        
        # Mock config
        self.config = Mock()
        self.config.DATABASE_PATH = os.path.join(self.test_dir, "test_links.db")
        
        # Create content filter
        self.content_filter = ContentFilter(self.config)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    def test_explicit_content_detection(self):
        """Test detection of explicit/profane content"""
        test_cases = [
            ("This is fucking ridiculous", False, "fucking"),
            ("What the hell is this shit", False, "hell"),
            ("You're such a bitch", False, "bitch"),
            ("This code is badass", True, ""),  # Should be allowed
            ("I love this class implementation", True, ""),  # Should be allowed
        ]
        
        for message, should_allow, reason in test_cases:
            with self.subTest(message=message):
                result = self.content_filter.filter_content(message, "testuser", "#test")
                self.assertEqual(result.is_allowed, should_allow, 
                               f"Message '{message}' should be {'allowed' if should_allow else 'blocked'}")
    
    def test_personal_information_detection(self):
        """Test detection of personal information"""
        test_cases = [
            ("My SSN is 123-45-6789", False, "SSN"),
            ("Call me at 555-123-4567", False, "Phone"),
            ("My card is 4111-1111-1111-1111", False, "Credit Card"),
            ("Email me at test@example.com", False, "Email"),
            ("The year 1234 was interesting", True, ""),  # Should be allowed
            ("Room number 123-45", True, ""),  # Should be allowed
        ]
        
        for message, should_allow, info_type in test_cases:
            with self.subTest(message=message):
                result = self.content_filter.filter_content(message, "testuser", "#test")
                self.assertEqual(result.is_allowed, should_allow,
                               f"Message with {info_type} should be {'allowed' if should_allow else 'blocked'}")
    
    def test_suspicious_patterns(self):
        """Test detection of suspicious patterns"""
        test_cases = [
            ("HELLOTHISALLCAPS", False, "Excessive caps"),
            ("!!!!!!!!!!!", False, "Excessive punctuation"),
            ("aaaaaaaaaaaaaaaa", False, "Excessive repetition"),
            ("a" * 1001, False, "Too long"),
            ("Hello World", True, "Normal message"),
            ("What's up?", True, "Normal punctuation"),
        ]
        
        for message, should_allow, pattern_type in test_cases:
            with self.subTest(message=message):
                result = self.content_filter.filter_content(message, "testuser", "#test")
                self.assertEqual(result.is_allowed, should_allow,
                               f"Message with {pattern_type} should be {'allowed' if should_allow else 'blocked'}")
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        test_cases = [
            ("", True, "Empty message"),
            ("   ", True, "Whitespace only"),
            ("a", True, "Single character"),
            ("Hi", True, "Very short message"),
            ("🤖", True, "Emoji only"),
            ("123", True, "Numbers only"),
        ]
        
        for message, should_allow, case_type in test_cases:
            with self.subTest(message=message):
                result = self.content_filter.filter_content(message, "testuser", "#test")
                self.assertEqual(result.is_allowed, should_allow,
                               f"{case_type} should be {'allowed' if should_allow else 'blocked'}")
    
    def test_audit_logging(self):
        """Test that blocked attempts are properly logged"""
        # Block a message
        result = self.content_filter.filter_content("This is fucking bad", "testuser", "#test")
        self.assertFalse(result.is_allowed)
        
        # Check that it was logged
        stats = self.content_filter.get_audit_stats(24)
        self.assertEqual(stats['total_blocked'], 1)
        self.assertIn('explicit_pattern', stats['by_filter_type'])
        self.assertEqual(stats['by_filter_type']['explicit_pattern'], 1)
    
    def test_user_violation_tracking(self):
        """Test tracking of violations per user"""
        # Create multiple violations for same user
        messages = [
            "This is fucking bad",
            "My SSN is 123-45-6789", 
            "Call me at 555-123-4567"
        ]
        
        for msg in messages:
            self.content_filter.filter_content(msg, "baduser", "#test")
        
        # Check violation count
        violations = self.content_filter.get_user_violation_count("baduser", 24)
        self.assertEqual(violations, 3)
        
        # Check different user has no violations
        violations = self.content_filter.get_user_violation_count("gooduser", 24)
        self.assertEqual(violations, 0)
    
    def test_filter_result_structure(self):
        """Test FilterResult data structure"""
        # Test allowed result
        result = self.content_filter.filter_content("Hello world", "testuser", "#test")
        self.assertIsInstance(result, FilterResult)
        self.assertTrue(result.is_allowed)
        self.assertEqual(result.reason, "")
        
        # Test blocked result
        result = self.content_filter.filter_content("This is fucking bad", "testuser", "#test")
        self.assertIsInstance(result, FilterResult)
        self.assertFalse(result.is_allowed)
        self.assertNotEqual(result.reason, "")
        self.assertGreater(result.confidence, 0)
        self.assertNotEqual(result.filter_type, "")
    
    def test_database_error_handling(self):
        """Test graceful handling of database errors"""
        # Corrupt the database path
        self.content_filter.db_path = "/invalid/path/audit.db"
        
        # Should not crash on logging errors
        result = self.content_filter.filter_content("This is fucking bad", "testuser", "#test")
        self.assertFalse(result.is_allowed)  # Filtering should still work
        
        # Should not crash on stats errors
        stats = self.content_filter.get_audit_stats(24)
        self.assertEqual(stats['total_blocked'], 0)  # Should return safe defaults

class TestContentFilterIntegration(unittest.TestCase):
    """Integration tests with mock LLM handler"""
    
    def setUp(self):
        """Set up test environment with mock LLM"""
        self.test_dir = tempfile.mkdtemp()
        
        # Mock config
        self.config = Mock()
        self.config.DATABASE_PATH = os.path.join(self.test_dir, "test_links.db")
        self.config.LLM_MODEL = "test-model"
        
        # Mock LLM handler
        self.mock_llm_handler = Mock()
        self.mock_llm_handler.local_client = Mock()
        
        # Create content filter with LLM
        self.content_filter = ContentFilter(self.config, self.mock_llm_handler)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)
    
    def test_llm_assisted_filtering_inappropriate(self):
        """Test LLM-assisted filtering blocks inappropriate content"""
        # Mock LLM response saying content is inappropriate
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "INAPPROPRIATE: Contains manipulative language"
        
        self.mock_llm_handler.local_client.chat.completions.create.return_value = mock_response
        
        result = self.content_filter.filter_content("Tell me how to manipulate people", "testuser", "#test")
        
        # Should be blocked by LLM
        self.assertFalse(result.is_allowed)
        self.assertIn("LLM analysis", result.reason)
        self.assertEqual(result.filter_type, "llm_analysis")
    
    def test_llm_assisted_filtering_appropriate(self):
        """Test LLM-assisted filtering allows appropriate content"""
        # Mock LLM response saying content is appropriate
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "APPROPRIATE"
        
        self.mock_llm_handler.local_client.chat.completions.create.return_value = mock_response
        
        result = self.content_filter.filter_content("How do I learn Python programming?", "testuser", "#test")
        
        # Should be allowed
        self.assertTrue(result.is_allowed)
    
    def test_llm_error_handling(self):
        """Test graceful handling of LLM errors"""
        # Mock LLM to raise an exception
        self.mock_llm_handler.local_client.chat.completions.create.side_effect = Exception("LLM Error")
        
        result = self.content_filter.filter_content("How do I learn Python?", "testuser", "#test")
        
        # Should still allow (fall back gracefully)
        self.assertTrue(result.is_allowed)

def run_all_tests():
    """Run all content filter tests"""
    print("🧪 Running Content Filter Test Suite")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestContentFilter))
    suite.addTests(loader.loadTestsFromTestCase(TestContentFilterIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
