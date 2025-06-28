#!/usr/bin/env python3
"""
Comprehensive Performance and Integration Testing
Tests LLM performance, timing, retry behavior, and bot integration.
"""

import sys
import unittest
import logging
import time
from unittest.mock import Mock, patch
from threading import Thread

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from bot import AircBot
from llm_handler import LLMHandler
from config import Config

class TestLLMPerformance(unittest.TestCase):
    """Test LLM performance tracking and statistics"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.config.LLM_ENABLED = True
        
        # Create LLM handler
        self.llm = LLMHandler(self.config)
        
        # Reset performance stats
        self.llm.response_times = []
        self.llm.total_requests = 0
        self.llm.failed_requests = 0
    
    def test_performance_statistics_tracking(self):
        """Test that performance statistics are tracked correctly"""
        if not self.llm.is_enabled():
            self.skipTest("LLM not available for testing")
        
        # Mock successful responses
        call_count = 0
        response_times = []
        
        def mock_timed_response(**kwargs):
            nonlocal call_count
            call_count += 1
            
            # Simulate different response times
            time.sleep(0.01)  # Small delay to simulate processing
            
            class MockMessage:
                def __init__(self, content):
                    self.content = content
                    
            class MockChoice:
                def __init__(self, content):
                    self.message = MockMessage(content)
                    
            class MockResponse:
                def __init__(self, content):
                    self.choices = [MockChoice(content)]
            
            return MockResponse(f"Response {call_count}")
        
        # Set up mock client
        self.llm.client = Mock()
        self.llm.client.chat.completions.create = mock_timed_response
        
        # Make several requests
        questions = ["test 1", "test 2", "test 3"]
        for question in questions:
            result = self.llm.ask_llm(question)
            self.assertIsNotNone(result)
        
        # Check statistics
        stats = self.llm.get_performance_stats()
        
        self.assertEqual(stats['total_requests'], 3)
        self.assertEqual(stats['failed_requests'], 0)
        self.assertEqual(stats['success_rate'], "100.0%")
        self.assertEqual(len(self.llm.response_times), 3)
        
        # All response times should be > 0
        for rt in self.llm.response_times:
            self.assertGreater(rt, 0)
    
    def test_failed_request_tracking(self):
        """Test that failed requests are tracked correctly"""
        if not self.llm.is_enabled():
            self.skipTest("LLM not available for testing")
        
        # Mock responses that alternate between empty and success
        call_count = 0
        
        def mock_mixed_responses(**kwargs):
            nonlocal call_count
            call_count += 1
            
            class MockMessage:
                def __init__(self, content):
                    self.content = content
                    
            class MockChoice:
                def __init__(self, content):
                    self.message = MockMessage(content)
                    
            class MockResponse:
                def __init__(self, content):
                    self.choices = [MockChoice(content)]
            
            # Return empty on odd calls, success on even calls
            if call_count % 2 == 1:
                return MockResponse("")  # Empty response (will fail)
            else:
                return MockResponse(f"Success {call_count}")
        
        self.llm.client = Mock()
        self.llm.client.chat.completions.create = mock_mixed_responses
        
        # Make several requests
        questions = ["test 1", "test 2"]
        for question in questions:
            result = self.llm.ask_llm(question)
            self.assertIsNotNone(result)
        
        # Check statistics - first call should have failed (3 attempts), second should succeed
        self.assertGreaterEqual(self.llm.failed_requests, 1)  # At least 1 failure from empty responses
        self.assertGreaterEqual(self.llm.total_requests, 1)   # At least 1 success
    
    def test_response_time_bounds(self):
        """Test that response times are within reasonable bounds"""
        if not self.llm.is_enabled():
            self.skipTest("LLM not available for testing")
        
        # Mock a simple fast response
        def mock_fast_response(**kwargs):
            class MockMessage:
                def __init__(self, content):
                    self.content = content
                    
            class MockChoice:
                def __init__(self, content):
                    self.message = MockMessage(content)
                    
            class MockResponse:
                def __init__(self, content):
                    self.choices = [MockChoice(content)]
            
            return MockResponse("Quick response")
        
        self.llm.client = Mock()
        self.llm.client.chat.completions.create = mock_fast_response
        
        start_time = time.time()
        result = self.llm.ask_llm("quick test")
        end_time = time.time()
        
        self.assertIsNotNone(result)
        
        # Response should be reasonably fast (under 1 second for mocked response)
        total_time = end_time - start_time
        self.assertLess(total_time, 1.0)
        
        # Should have recorded timing
        self.assertGreater(len(self.llm.response_times), 0)
        self.assertGreater(self.llm.response_times[-1], 0)

class TestBotIntegration(unittest.TestCase):
    """Test bot integration and command handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = AircBot()
        
        # Create mock connection
        self.connection = Mock()
        self.connection.privmsg = Mock()
        self.connection.get_nickname = Mock(return_value="testbot")
        
        self.channel = "#test"
    
    def test_performance_command(self):
        """Test the !performance command"""
        if not self.bot.llm_handler.is_enabled():
            self.skipTest("LLM not available for testing")
        
        # Set up some mock performance data
        self.bot.llm_handler.total_requests = 10
        self.bot.llm_handler.failed_requests = 2
        self.bot.llm_handler.response_times = [1.0, 1.5, 0.8, 2.0, 1.2]
        
        # Call the performance command
        self.bot.show_performance_stats(self.connection, self.channel)
        
        # Check that privmsg was called with performance stats
        calls = self.connection.privmsg.call_args_list
        self.assertGreater(len(calls), 0)
        
        # Should have sent multiple lines of stats
        stat_messages = [call[0][1] for call in calls]
        stats_text = " ".join(stat_messages)
        
        self.assertIn("Performance Stats", stats_text)
        self.assertIn("Total requests", stats_text)
        self.assertIn("Failed requests", stats_text)
        self.assertIn("Success rate", stats_text)
        self.assertIn("response time", stats_text)
    
    def test_llm_unavailable_performance_command(self):
        """Test performance command when LLM is unavailable"""
        # Temporarily disable LLM
        original_enabled = self.bot.llm_handler.enabled
        self.bot.llm_handler.enabled = False
        
        try:
            self.bot.show_performance_stats(self.connection, self.channel)
            
            # Should have sent an error message
            calls = self.connection.privmsg.call_args_list
            self.assertGreater(len(calls), 0)
            
            error_message = calls[0][0][1]
            self.assertIn("not available", error_message)
            
        finally:
            # Restore original state
            self.bot.llm_handler.enabled = original_enabled
    
    def test_ask_command_timing(self):
        """Test that ask command processing time is logged"""
        if not self.bot.llm_handler.is_enabled():
            self.skipTest("LLM not available for testing")
        
        # Mock the LLM to return quickly
        def mock_quick_response(**kwargs):
            class MockMessage:
                def __init__(self, content):
                    self.content = content
                    
            class MockChoice:
                def __init__(self, content):
                    self.message = MockMessage(content)
                    
            class MockResponse:
                def __init__(self, content):
                    self.choices = [MockChoice(content)]
            
            return MockResponse("Quick test response")
        
        self.bot.llm_handler.client = Mock()
        self.bot.llm_handler.client.chat.completions.create = mock_quick_response
        
        # Capture log output
        with patch('logging.Logger.info') as mock_log:
            # Process ask request directly (not in thread for testing)
            self.bot._process_ask_request(self.connection, self.channel, "testuser", "test question")
            
            # Check that timing was logged
            log_calls = [call[0][0] for call in mock_log.call_args_list]
            timing_logs = [log for log in log_calls if "processing time" in log]
            self.assertGreater(len(timing_logs), 0)
    
    def test_rate_limited_commands(self):
        """Test that commands are properly rate limited"""
        # Set a very restrictive rate limit for testing
        from rate_limiter import RateLimiter
        self.bot.rate_limiter = RateLimiter(user_limit_per_minute=1, total_limit_per_minute=2)
        
        user = "testuser"
        
        # First command should work
        self.bot.handle_command(self.connection, self.channel, user, "!help")
        help_calls = len(self.connection.privmsg.call_args_list)
        self.assertGreater(help_calls, 0)
        
        # Second command should be rate limited
        self.connection.privmsg.reset_mock()
        self.bot.handle_command(self.connection, self.channel, user, "!links")
        
        # Should have gotten a rate limit message instead
        calls = self.connection.privmsg.call_args_list
        self.assertGreater(len(calls), 0)
        
        rate_limit_message = calls[0][0][1]
        self.assertIn("wait a moment", rate_limit_message.lower())

class TestRealLLMTiming(unittest.TestCase):
    """Test actual LLM timing with real requests (if LLM is available)"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.llm = LLMHandler(self.config)
    
    def test_real_llm_response_times(self):
        """Test actual LLM response times for different question types"""
        if not self.llm.is_enabled():
            self.skipTest("LLM not available for real timing tests")
        
        print("\n🔄 Testing real LLM response times...")
        
        test_questions = [
            ("hello", "Simple greeting"),
            ("what is 2+2?", "Simple math"),
            ("name three colors", "Simple list"),
            ("what are three mountain ranges in the US?", "Geographic list"),
        ]
        
        results = []
        
        for question, description in test_questions:
            print(f"Testing: {description} - '{question}'")
            
            start_time = time.time()
            response = self.llm.ask_llm(question)
            end_time = time.time()
            
            response_time = end_time - start_time
            results.append((description, question, response_time, response))
            
            print(f"  Time: {response_time:.2f}s")
            print(f"  Response: {response[:60]}...")
            
            # Reasonable time bounds
            self.assertLess(response_time, 30.0, f"Response took too long: {response_time:.2f}s")
            self.assertIsNotNone(response, "Should have gotten a response")
        
        # Print summary
        print(f"\n📊 Timing Summary:")
        for description, question, response_time, response in results:
            print(f"  {description}: {response_time:.2f}s")
        
        avg_time = sum(rt for _, _, rt, _ in results) / len(results)
        print(f"  Average: {avg_time:.2f}s")

def run_performance_tests():
    """Run all performance tests"""
    print("⚡ Running Comprehensive Performance Tests")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestLLMPerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestBotIntegration))
    
    # Add real LLM tests only if specifically requested
    if "--real-llm" in sys.argv:
        suite.addTests(loader.loadTestsFromTestCase(TestRealLLMTiming))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All performance tests passed!")
        return True
    else:
        print("❌ Some performance tests failed!")
        return False

if __name__ == "__main__":
    print("Performance Testing Suite")
    print("Usage: python test_performance.py [--real-llm]")
    print("  --real-llm: Include tests that make actual LLM requests")
    print()
    
    success = run_performance_tests()
    sys.exit(0 if success else 1)
