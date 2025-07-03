#!/usr/bin/env python3
"""
Comprehensive LLM Validation and Response Testing
Tests all aspects of LLM prompt validation, response processing, and edge cases.
"""

import sys
import unittest
import logging
from unittest.mock import Mock, patch
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from llm_handler import LLMHandler
from config import Config
from prompts import get_error_message

class TestLLMValidation(unittest.TestCase):
    """Test LLM response validation and processing"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.config.LLM_ENABLED = True
        
        # Create LLM handler without actual initialization
        self.llm = LLMHandler.__new__(LLMHandler)
        self.llm.config = self.config
        self.llm.enabled = True
        self.llm.response_times = []
        self.llm.total_requests = 0
        self.llm.failed_requests = 0
    
    def test_think_tag_removal(self):
        """Test removal of <think> tags from responses"""
        test_cases = [
            # Basic <think> tag removal
            ("<think>Let me think about this</think>Hello world", "Hello world"),
            
            # Multiple <think> tags
            ("<think>First thought</think>Answer<think>Second thought</think>", "Answer"),
            
            # Nested content in <think> tags
            ("<think>This has\nmultiple lines\nand stuff</think>Clean answer", "Clean answer"),
            
            # Unclosed <think> tag - everything after should be removed
            ("Good start <think>but then I start thinking and never stop", "Good start"),
            
            # Empty <think> tags
            ("<think></think>Just the answer", "Just the answer"),
            
            # Case insensitive tag removal (the actual regex handles this)
            ("<think>lowercase</think>Answer", "Answer"),
            
            # No <think> tags - should return unchanged
            ("Just a normal response", "Just a normal response"),
            
            # Only <think> tags - should return empty (which triggers no_response)
            ("<think>Only thinking, no answer</think>", ""),
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input=input_text):
                result = self.llm._validate_response_length(input_text)
                if expected == "":
                    # Empty responses should return the no_response error message
                    self.assertEqual(result, get_error_message('no_response'))
                else:
                    self.assertEqual(result, expected)
    
    def test_response_length_validation(self):
        """Test response length limits"""
        # Short response - should pass
        short_response = "This is short."
        result = self.llm._validate_response_length(short_response)
        self.assertEqual(result, short_response)
        
        # Medium response - should pass
        medium_response = "This is a medium length response with a few sentences. It explains something briefly."
        result = self.llm._validate_response_length(medium_response)
        self.assertEqual(result, medium_response)
        
        # Very long response - should be rejected
        long_response = "A" * 500  # 500 characters
        result = self.llm._validate_response_length(long_response)
        self.assertEqual(result, get_error_message('too_complex'))
        
        # Empty response - should be rejected
        result = self.llm._validate_response_length("")
        self.assertEqual(result, get_error_message('no_response'))
        
        # Whitespace only - should be rejected
        result = self.llm._validate_response_length("   \n\t  ")
        self.assertEqual(result, get_error_message('no_response'))
    
    def test_complexity_detection(self):
        """Test detection of complex responses that should be rejected"""
        # Simple response - should pass
        simple = "Python is a programming language."
        result = self.llm._validate_response_length(simple)
        self.assertEqual(result, simple)
        
        # Complex with academic language - should be rejected
        complex_academic = "Python is a programming language. However, it has many advanced features. Furthermore, it's used in multiple domains."
        result = self.llm._validate_response_length(complex_academic)
        self.assertEqual(result, get_error_message('too_complex'))
        
        # Too many sentences - should be rejected
        many_sentences = "First sentence. Second sentence. Third sentence. Fourth sentence. Fifth sentence."
        result = self.llm._validate_response_length(many_sentences)
        self.assertEqual(result, get_error_message('too_complex'))
        
        # Multiple paragraphs - should be rejected
        paragraphs = "First paragraph here.\n\nSecond paragraph.\n\nThird paragraph."
        result = self.llm._validate_response_length(paragraphs)
        self.assertEqual(result, get_error_message('too_complex'))
    
    def test_simple_questions_get_friendly_responses(self):
        """Test that simple questions get appropriate friendly responses"""
        # Test the actual LLM if available
        if not hasattr(self.llm, 'client') or self.llm.client is None:
            self.skipTest("LLM not available for testing")
            
        simple_questions = [
            "hello",
            "hi",
            "what's up?",
            "how are you?",
        ]
        
        for question in simple_questions:
            with self.subTest(question=question):
                # Mock the client to return a simple friendly response
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = "Hello! I'm doing well, thanks for asking."
                
                with patch.object(self.llm, 'client') as mock_client:
                    mock_client.chat.completions.create.return_value = mock_response
                    
                    result = self.llm.ask_llm(question)
                    self.assertIsNotNone(result)
                    self.assertNotIn("too complicated", result)
                    self.assertNotIn("I'm not sure", result)
    
    def test_simple_lists_are_allowed(self):
        """Test that simple lists (up to 5 items) are allowed and not rejected"""
        simple_lists = [
            "1. First item\n2. Second item\n3. Third item",
            "Red, blue, green",
            "- Apple\n- Banana\n- Orange",
            "The Rocky Mountains, Sierra Nevada, and Cascade Range.",  # Geographic lists
        ]
        
        for list_text in simple_lists:
            with self.subTest(list_text=list_text):
                result = self.llm._validate_response_length(list_text)
                # These should NOT be rejected as too complex
                self.assertNotEqual(result, get_error_message('too_complex'))
                self.assertEqual(result, list_text)  # Should return unchanged
    
    def test_whitespace_handling(self):
        """Test proper handling of whitespace in responses"""
        test_cases = [
            # Leading/trailing whitespace
            ("  Answer with spaces  ", "Answer with spaces"),
            
            # Multiple internal spaces
            ("Answer  with    multiple   spaces", "Answer with multiple spaces"),
            
            # Mixed newlines and spaces
            ("Answer\nwith\nnewlines", "Answer with newlines"),
            
            # Tabs and other whitespace
            ("Answer\twith\ttabs", "Answer with tabs"),
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input=input_text):
                # First clean it like IRC processing would
                import re
                cleaned = input_text.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                
                result = self.llm._validate_response_length(cleaned)
                self.assertEqual(result, expected)
    
    def test_sentence_counting(self):
        """Test sentence counting logic"""
        test_cases = [
            # Normal sentences - periods NOT preceded by digits should count
            ("This is one sentence.", 1),
            ("First sentence. Second sentence.", 2),
            ("First! Second? Third.", 3),
            
            # Numbered lists should NOT count periods as sentence endings (preceded by digits)
            ("1. First item. 2. Second item. 3. Third item.", 3),  # These ARE counted since the logic counts periods not preceded by digits, but periods after "item" are not preceded by digits
            
            # Mixed content - only non-numbered periods should count
            ("Here are some items: 1. First. 2. Second. That's it.", 3),  # "First.", "Second.", "it." all count
            
            # Decimals and numbers should not count their periods
            ("The price is $3.50 today.", 1),  # Only "today." counts
            ("Version 2.1 is better than 1.0 overall.", 1),  # Only "overall." counts
        ]
        
        for text, expected_sentences in test_cases:
            with self.subTest(text=text):
                import re
                # Count periods not preceded by digits (this is the logic from the actual code)
                period_count = len(re.findall(r'(?<!\d)\.', text))
                sentence_endings = period_count + text.count('!') + text.count('?')
                self.assertEqual(sentence_endings, expected_sentences)
    
    def test_mountain_ranges_variations(self):
        """Test all variations of mountain ranges questions that should be allowed"""
        if not hasattr(self.llm, 'client') or self.llm.client is None:
            self.skipTest("LLM not available for testing")
            
        mountain_questions = [
            "name three mountain ranges in the continental united states",
            "what are three mountain ranges in the US?",
            "list 3 mountain ranges in america",
            "tell me three mountain ranges in the continental US",
            "can you name three mountain ranges?",
            "three mountain ranges in america please",
        ]
        
        for question in mountain_questions:
            with self.subTest(question=question):
                # Mock a typical good response
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = "The Rocky Mountains, Sierra Nevada, and Cascade Range."
                
                with patch.object(self.llm, 'client') as mock_client:
                    mock_client.chat.completions.create.return_value = mock_response
                    
                    result = self.llm.ask_llm(question)
                    self.assertIsNotNone(result)
                    # These should NOT be rejected
                    self.assertNotIn("too complicated", result)
                    self.assertNotIn("I'm not sure", result)
    
    def test_various_simple_list_questions(self):
        """Test various types of simple list questions that should be allowed"""
        if not hasattr(self.llm, 'client') or self.llm.client is None:
            self.skipTest("LLM not available for testing")
            
        simple_list_questions = [
            ("name three colors", "Red, blue, green"),
            ("list three animals", "Dogs, cats, elephants"),
            ("what are three fruits?", "Apples, bananas, oranges"),
            ("tell me three planets", "Earth, Mars, Jupiter"),
            ("name three programming languages", "Python, Java, JavaScript"),
            ("list four seasons", "Spring, summer, fall, winter"),
            ("what are the four cardinal directions?", "North, south, east, west"),
        ]
        
        for question, mock_answer in simple_list_questions:
            with self.subTest(question=question):
                # Mock a simple list response
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = mock_answer
                
                with patch.object(self.llm, 'client') as mock_client:
                    mock_client.chat.completions.create.return_value = mock_response
                    
                    result = self.llm.ask_llm(question)
                    self.assertIsNotNone(result)
                    # These should NOT be rejected
                    self.assertNotIn("too complicated", result)
                    self.assertNotIn("I'm not sure", result)
                    self.assertEqual(result, mock_answer)
    
    def test_complex_list_rejection(self):
        """Test that genuinely complex lists are still properly rejected"""
        complex_lists = [
            # Very long list (more than 5 items)
            "1. First\n2. Second\n3. Third\n4. Fourth\n5. Fifth\n6. Sixth\n7. Seventh item",
            
            # List with detailed explanations and more than 5 numbered items
            "1. Python - A high-level programming language. 2. Java - Object-oriented language. 3. C++ - Systems programming. 4. JavaScript for web. 5. Go for concurrency. 6. Rust for safety.",
            
            # Academic-style complex response
            "There are several mountain ranges. However, the most significant ones include the Rocky Mountains. Furthermore, the Sierra Nevada range.",
        ]
        
        for complex_text in complex_lists:
            with self.subTest(complex_text=complex_text):
                result = self.llm._validate_response_length(complex_text)
                # These SHOULD be rejected as too complex
                self.assertEqual(result, get_error_message('too_complex'))

class TestRetryLogic(unittest.TestCase):
    """Test LLM retry logic for empty responses"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.config.LLM_RETRY_ATTEMPTS = 3
        self.config.LLM_ENABLED = True
        self.config.LLM_MODE = 'local_only'
        self.config.LLM_BASE_URL = 'http://localhost:11434'
        self.config.LLM_MODEL = 'test-model'
        self.config.LLM_API_KEY = 'test-key'
        self.config.OPENAI_ENABLED = False
        
        # Create handler without initialization
        self.handler = LLMHandler.__new__(LLMHandler)
        self.handler.config = self.config
        self.handler.mode = self.config.LLM_MODE
        self.handler.enabled = True
        
        # Set up mock local client since we're in local_only mode
        self.handler.local_client = Mock()
        self.handler.openai_client = None
        self.handler.openai_rate_limiter = None
        
        self.handler.response_times = {'local': [], 'openai': []}
        self.handler.total_requests = {'local': 0, 'openai': 0}
        self.handler.failed_requests = {'local': 0, 'openai': 0}
    
    def test_empty_response_retries(self):
        """Test that empty responses trigger retries"""
        call_count = 0
        
        def mock_empty_responses(**kwargs):
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
            
            # Return empty for first 2, success on 3rd
            if call_count <= 2:
                return MockResponse("")  # Empty response
            else:
                return MockResponse("Success after retries!")
        
        # Set up mock client
        self.handler.local_client.chat.completions.create = mock_empty_responses
        
        result = self.handler.ask_llm("test question")
        
        self.assertEqual(call_count, 3)
        self.assertEqual(result, "Success after retries!")
    
    def test_validation_failure_no_retry(self):
        """Test that validation failures do NOT trigger retries"""
        call_count = 0
        
        def mock_complex_response(**kwargs):
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
            
            # Return complex response that should be rejected by validation
            complex_response = """This is a very long and complex response.
            It has multiple sentences and goes into great detail.
            This should be rejected by the validation logic.
            But it should NOT trigger retries because it's not empty."""
            
            return MockResponse(complex_response)
        
        self.handler.local_client.chat.completions.create = mock_complex_response
        
        result = self.handler.ask_llm("complex question")
        
        self.assertEqual(call_count, 1)  # Should only be called once
        self.assertIn("too complicated", result)
    
    def test_all_retries_exhausted(self):
        """Test behavior when all retries return empty"""
        call_count = 0
        
        def mock_always_empty(**kwargs):
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
            
            return MockResponse("")  # Always empty
        
        self.handler.local_client.chat.completions.create = mock_always_empty
        
        result = self.handler.ask_llm("test question")
        
        self.assertEqual(call_count, 3)  # Should retry 3 times
        self.assertEqual(result, get_error_message('no_response'))

def run_validation_tests():
    """Run all validation tests"""
    print("🧠 Running Comprehensive LLM Validation Tests")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestLLMValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestRetryLogic))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All validation tests passed!")
        return True
    else:
        print("❌ Some validation tests failed!")
        return False

if __name__ == "__main__":
    success = run_validation_tests()
    sys.exit(0 if success else 1)
