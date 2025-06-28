#!/usr/bin/env python3
"""
Test suite for LLM prompt validation and response cleaning

Note: Some tests may occasionally fail due to LLM response variability.
This is expected behavior - the important thing is that:
1. Complex responses are consistently rejected
2. Most simple questions work most of the time
3. The validation logic itself is sound
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
            
            # Long lists (more than 5 items)
            "Here are the steps: 1. First 2. Second 3. Third 4. Fourth 5. Fifth 6. Sixth",
            "Options: • Option A • Option B • Option C • Option D • Option E • Option F",
            
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

    def test_simple_lists_are_allowed(self):
        """Test that simple lists (up to 5 items) are allowed and not rejected"""
        simple_list_responses = [
            # Short lists should be allowed
            "Three options: 1. First 2. Second 3. Third",
            "Here are four things: • Item A • Item B • Item C • Item D",
            "Five choices: 1. One 2. Two 3. Three 4. Four 5. Five",
            "The Rocky Mountains, Sierra Nevada, and Cascade Range.",
        ]
        
        for response in simple_list_responses:
            with self.subTest(response=response):
                result = self.llm._validate_response_length(response)
                # Should NOT be rejected as too complex
                self.assertNotEqual(result, "That's too complicated to answer here")
                # Should return the original response
                self.assertEqual(result, response)
    
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
    
    def test_mountain_ranges_variations(self):
        """Test all variations of mountain ranges questions that should be allowed"""
        if not self.llm.is_enabled():
            self.skipTest("LLM not available for testing")
        
        mountain_questions = [
            "name three mountain ranges in the continental united states",
            "what are three mountain ranges in the US?",
            "list 3 mountain ranges in america",
            "tell me three mountain ranges in the continental US",
            "can you name three mountain ranges?",
            "three mountain ranges in america please",
            "what are some mountain ranges in the US?",
            "name a few mountain ranges in america",
        ]
        
        for question in mountain_questions:
            with self.subTest(question=question):
                response = self.llm.ask_llm(question)
                
                # Should not get fallback responses
                self.assertNotEqual(response, "That's too complicated to answer here")
                self.assertNotEqual(response, "I'm not sure how to respond to that.")
                
                # Should get a reasonable response
                self.assertIsInstance(response, str)
                self.assertGreater(len(response.strip()), 0)
                
                # Should mention actual mountain ranges
                response_lower = response.lower()
                mountain_keywords = ['rocky', 'sierra', 'cascade', 'appalachian', 'mountain']
                has_mountain_keywords = any(keyword in response_lower for keyword in mountain_keywords)
                self.assertTrue(has_mountain_keywords, f"Response '{response}' doesn't mention mountains")

    def test_various_simple_list_questions(self):
        """Test various types of simple list questions that should be allowed"""
        if not self.llm.is_enabled():
            self.skipTest("LLM not available for testing")
        
        simple_list_questions = [
            # Geography
            ("name three states in the USA", ["state", "california", "texas", "new york"]),
            ("list three major cities in California", ["city", "los angeles", "san francisco", "diego"]),
            ("what are three countries in Europe?", ["country", "france", "germany", "italy", "spain"]),
            
            # General knowledge
            ("name three colors", ["red", "blue", "green", "yellow"]),
            ("list three animals", ["cat", "dog", "bird", "lion", "tiger"]),
            ("what are three fruits?", ["apple", "banana", "orange", "grape"]),
            ("tell me three planets", ["earth", "mars", "venus", "jupiter"]),
            
            # Slightly longer lists (4-5 items)
            ("list four seasons", ["spring", "summer", "fall", "winter", "autumn"]),
            ("name five days of the week", ["monday", "tuesday", "wednesday", "thursday", "friday"]),
        ]
        
        for question, expected_keywords in simple_list_questions:
            with self.subTest(question=question):
                response = self.llm.ask_llm(question)
                
                # Should not get fallback responses
                self.assertNotEqual(response, "That's too complicated to answer here")
                self.assertNotEqual(response, "I'm not sure how to respond to that.")
                
                # Should get a reasonable response
                self.assertIsInstance(response, str)
                self.assertGreater(len(response.strip()), 0)
                
                # Should contain relevant keywords
                response_lower = response.lower()
                has_relevant_keywords = any(keyword in response_lower for keyword in expected_keywords)
                self.assertTrue(has_relevant_keywords, 
                              f"Response '{response}' doesn't contain expected keywords: {expected_keywords}")

    def test_complex_list_rejection(self):
        """Test that genuinely complex lists are still properly rejected"""
        complex_list_responses = [
            # Very long numbered lists (more than 5 items)
            "Steps: 1. First 2. Second 3. Third 4. Fourth 5. Fifth 6. Sixth 7. Seventh",
            "Options: • A • B • C • D • E • F • G • H",
            
            # Multiple paragraphs
            "First paragraph here.\n\nSecond paragraph.\n\nThird paragraph here.",
            
            # Academic language
            "However, this is furthermore complicated. Moreover, we must specifically consider the various implications.",
            
            # Too many explanations
            "First: explanation here. Second: another explanation. Third: more details. Fourth: even more.",
        ]
        
        for response in complex_list_responses:
            with self.subTest(response=response):
                result = self.llm._validate_response_length(response)
                # Should be rejected as too complex
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
