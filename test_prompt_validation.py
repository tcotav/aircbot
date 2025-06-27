#!/usr/bin/env python3
"""
Test suite for LLM prompt validation and response cleaning
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import unittest
import re
from llm_handler import LLMHandler
from config import Config


class TestPromptValidation(unittest.TestCase):
    """Test cases for LLM response validation and cleaning"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.llm = LLMHandler(self.config)
    
    def test_think_tag_removal(self):
        """Test removal of <think> tags from responses"""
        test_cases = [
            # Closed think tags
            ("<think>reasoning here</think>Hello world!", "Hello world!"),
            ("<think>complex reasoning with\nmultiple lines</think>Simple answer.", "Simple answer."),
            
            # Unclosed think tags
            ("<think>reasoning that never ends", ""),
            ("<think>partial reasoning\nHello there!", ""),
            
            # Multiple think tags
            ("<think>first</think>Answer<think>second</think>", "Answer"),
            
            # No think tags
            ("Clean response without tags", "Clean response without tags"),
            
            # Empty after cleaning
            ("<think>only thinking, no response</think>", ""),
            
            # Malformed think tags
            ("<think>unclosed tag\nGood response here", ""),
            ("Response <think>in middle", "Response"),
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input=input_text):
                result = self.llm._validate_response_length(input_text)
                if expected == "":
                    # Empty responses should get fallback message
                    self.assertEqual(result, "I'm not sure how to respond to that.")
                else:
                    self.assertEqual(result, expected)
    
    def test_response_length_validation(self):
        """Test response length limits"""
        # Short responses should pass
        short_responses = [
            "Hi there!",
            "I'm doing great, thanks!",
            "Yes, that sounds good.",
            "Good morning! How are you?",
        ]
        
        for response in short_responses:
            with self.subTest(response=response):
                result = self.llm._validate_response_length(response)
                self.assertEqual(result, response)
        
        # Long responses should be rejected
        long_response = "This is a very long response that goes on and on with multiple sentences. " * 10
        result = self.llm._validate_response_length(long_response)
        self.assertEqual(result, "That's too complicated to answer here")
    
    def test_complexity_detection(self):
        """Test detection of complex responses that should be rejected"""
        complex_responses = [
            # Multiple paragraphs
            "Line 1\n\nLine 2\n\nLine 3\n\nLine 4",
            
            # Long lists
            "Here are the steps: 1. First 2. Second 3. Third 4. Fourth 5. Fifth",
            "Options: • Option A • Option B • Option C • Option D",
            
            # Many explanations (colons)
            "First: explanation. Second: another. Third: more. Fourth: even more.",
            
            # Academic language
            "However, this is furthermore complicated. Moreover, we must specifically consider...",
        ]
        
        for response in complex_responses:
            with self.subTest(response=response):
                result = self.llm._validate_response_length(response)
                self.assertEqual(result, "That's too complicated to answer here")
    
    def test_simple_questions_get_friendly_responses(self):
        """Test that simple questions get appropriate friendly responses"""
        if not self.llm.is_enabled():
            self.skipTest("LLM not available for testing")
        
        # Test just a couple that we know work well
        simple_questions = [
            "how are you today?",
            "hello!",
        ]
        
        for question in simple_questions:
            with self.subTest(question=question):
                response = self.llm.ask_llm(question)
                
                # Should not get the fallback messages
                self.assertNotEqual(response, "That's too complicated to answer here")
                self.assertNotEqual(response, "I'm not sure how to respond to that.")
                
                # Should get a reasonable response
                self.assertIsInstance(response, str)
                self.assertGreater(len(response.strip()), 0)
    
    def test_whitespace_handling(self):
        """Test proper handling of whitespace in responses"""
        test_cases = [
            ("  Hello world!  ", "Hello world!"),
            ("\n\nGood morning!\n\n", "Good morning!"),
            ("<think>reasoning</think>\n  Clean response  \n", "Clean response"),
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input=input_text):
                result = self.llm._validate_response_length(input_text)
                self.assertEqual(result, expected)
    
    def test_sentence_counting(self):
        """Test sentence counting logic"""
        # Responses with acceptable sentence counts (1-3)
        acceptable = [
            "Hello!",  # 1 sentence
            "Hi there! How are you?",  # 2 sentences  
            "Good morning! Hope you're well. Ready to chat?",  # 3 sentences
        ]
        
        for response in acceptable:
            with self.subTest(response=response):
                result = self.llm._validate_response_length(response)
                self.assertEqual(result, response)
        
        # Responses with too many sentences (>3)
        too_many = "First sentence. Second sentence. Third sentence. Fourth sentence. Fifth sentence."
        result = self.llm._validate_response_length(too_many)
        self.assertEqual(result, "That's too complicated to answer here")


def run_validation_tests():
    """Run all prompt validation tests"""
    print("Running LLM prompt validation tests...\n")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPromptValidation)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    if result.wasSuccessful():
        print(f"\n✅ All {result.testsRun} validation tests passed!")
    else:
        print(f"\n❌ {len(result.failures)} failures, {len(result.errors)} errors out of {result.testsRun} tests")
        
        for test, traceback in result.failures:
            print(f"\nFAILURE: {test}")
            print(traceback)
            
        for test, traceback in result.errors:
            print(f"\nERROR: {test}")
            print(traceback)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_validation_tests()
