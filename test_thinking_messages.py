#!/usr/bin/env python3
"""
Test to verify thinking message duplication is fixed
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot import AircBot
from config import Config
import unittest
from unittest.mock import Mock, MagicMock

class TestThinkingMessages(unittest.TestCase):
    """Test that thinking messages are not duplicated"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.bot = AircBot()
        
        # Mock connection and channel
        self.mock_connection = Mock()
        self.mock_connection.privmsg = Mock()
        self.channel = "#test"
        self.user = "testuser"
    
    def test_ask_command_shows_thinking_once(self):
        """Test that !ask command shows thinking message once"""
        question = "what is the capital of italy?"
        
        # Call handle_ask_command
        self.bot.handle_ask_command(self.mock_connection, self.channel, self.user, question)
        
        # Check that privmsg was called (at least once for thinking message)
        self.assertTrue(self.mock_connection.privmsg.called)
        
        # Find thinking messages
        thinking_calls = [call for call in self.mock_connection.privmsg.call_args_list 
                         if len(call[0]) > 1 and "🤔" in str(call[0][1])]
        
        print(f"Ask command - Thinking message calls: {len(thinking_calls)}")
        for call in thinking_calls:
            print(f"  Message: {call[0][1]}")
        
        # Should have exactly one thinking message
        self.assertEqual(len(thinking_calls), 1)
    
    def test_ask_command_with_show_thinking_false(self):
        """Test that !ask command with show_thinking=False shows no thinking message"""
        question = "what is the capital of italy?"
        
        # Call handle_ask_command with show_thinking=False
        self.bot.handle_ask_command(self.mock_connection, self.channel, self.user, question, show_thinking=False)
        
        # Check calls made
        calls = self.mock_connection.privmsg.call_args_list
        
        # Find thinking messages
        thinking_calls = [call for call in calls if len(call[0]) > 1 and "🤔" in str(call[0][1])]
        
        print(f"Ask command (no thinking) - Thinking message calls: {len(thinking_calls)}")
        
        # Should have no thinking messages
        self.assertEqual(len(thinking_calls), 0)

def run_thinking_tests():
    """Run thinking message tests"""
    print("🧪 Testing Thinking Message Duplication Fix")
    print("=" * 50)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestThinkingMessages)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print(f"\n✅ All {result.testsRun} thinking message tests passed!")
    else:
        print(f"\n❌ {len(result.failures)} failures, {len(result.errors)} errors")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    run_thinking_tests()
