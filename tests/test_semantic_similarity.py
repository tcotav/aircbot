#!/usr/bin/env python3
"""
Tests for semantic similarity functionality in the fallback system
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import tempfile
import shutil

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from semantic_similarity import SemanticSimilarityScorer
from llm_handler import LLMHandler


class MockConfig:
    """Mock configuration for testing"""
    def __init__(self, semantic_enabled=True):
        # Semantic similarity settings
        self.SEMANTIC_SIMILARITY_ENABLED = semantic_enabled
        self.SEMANTIC_SIMILARITY_MIN_THRESHOLD = 0.3
        self.SEMANTIC_SIMILARITY_WEIGHT = 0.4
        self.SEMANTIC_MODEL_NAME = 'all-MiniLM-L6-v2'
        self.SEMANTIC_MODEL_DEVICE = 'cpu'
        self.SEMANTIC_CACHE_SIZE = 10
        self.SEMANTIC_CONTEXT_ENABLED = True
        self.SEMANTIC_CONTEXT_WEIGHT = 0.2
        self.SEMANTIC_ENTITY_BOOST = 1.2
        self.SEMANTIC_TECHNICAL_KEYWORDS = ['code', 'function', 'python', 'javascript', 'api', 'database', 'server', 'test']
        
        # Other config needed for tests
        self.LLM_MODE = 'fallback'
        self.LLM_ENABLED = True
        self.OPENAI_ENABLED = True
        self.IRC_NICKNAME = 'testbot'


class TestSemanticSimilarityScorer(unittest.TestCase):
    """Test semantic similarity scoring functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = MockConfig()
        self.scorer = SemanticSimilarityScorer(self.config)
    
    def test_initialization_disabled(self):
        """Test initialization when semantic similarity is disabled"""
        config = MockConfig(semantic_enabled=False)
        scorer = SemanticSimilarityScorer(config)
        self.assertFalse(scorer.is_available())
        self.assertFalse(scorer.model_loaded)
    
    def test_initialization_enabled(self):
        """Test initialization when semantic similarity is enabled"""
        # This test depends on sentence-transformers being installed
        if not self.scorer.is_available():
            self.skipTest("sentence-transformers not available")
        
        self.assertTrue(self.scorer.is_available())
        self.assertTrue(self.scorer.model_loaded)
    
    def test_compute_similarity_disabled(self):
        """Test similarity computation when disabled"""
        config = MockConfig(semantic_enabled=False)
        scorer = SemanticSimilarityScorer(config)
        
        similarity = scorer.compute_similarity("hello world", "hello universe")
        self.assertEqual(similarity, 0.0)
    
    def test_compute_similarity_enabled(self):
        """Test similarity computation when enabled"""
        if not self.scorer.is_available():
            self.skipTest("sentence-transformers not available")
        
        # Test similar texts
        similarity = self.scorer.compute_similarity("hello world", "hello universe")
        self.assertGreater(similarity, 0.3)
        
        # Test dissimilar texts
        similarity = self.scorer.compute_similarity("hello world", "car engine repair")
        self.assertLess(similarity, 0.3)
    
    def test_entity_boost_calculation(self):
        """Test technical keyword entity boost calculation"""
        question = "How do I write a Python function?"
        response = "To write a Python function, use the def keyword followed by the function name."
        
        boost = self.scorer._compute_entity_boost(question, response)
        self.assertGreater(boost, 1.0)  # Should get boost for technical terms
        
        # Test non-technical question
        question = "What's the weather like?"
        response = "It's sunny today."
        
        boost = self.scorer._compute_entity_boost(question, response)
        self.assertEqual(boost, 1.0)  # No technical terms, no boost
    
    def test_score_response_relevance(self):
        """Test comprehensive response relevance scoring"""
        if not self.scorer.is_available():
            self.skipTest("sentence-transformers not available")
        
        question = "How do I create a Python function?"
        good_response = "To create a Python function, use the def keyword followed by the function name and parameters."
        bad_response = "The weather is nice today."
        
        good_scores = self.scorer.score_response_relevance(question, good_response)
        bad_scores = self.scorer.score_response_relevance(question, bad_response)
        
        self.assertTrue(good_scores['available'])
        self.assertGreater(good_scores['combined_score'], bad_scores['combined_score'])
        self.assertTrue(good_scores['passes_threshold'])
        self.assertFalse(bad_scores['passes_threshold'])
    
    def test_should_fallback(self):
        """Test fallback decision logic"""
        if not self.scorer.is_available():
            self.skipTest("sentence-transformers not available")
        
        question = "How do I create a Python function?"
        good_response = "To create a Python function, use the def keyword followed by the function name and parameters."
        bad_response = "I don't know about that topic."
        
        # Good response should not trigger fallback
        self.assertFalse(self.scorer.should_fallback(question, good_response))
        
        # Bad response should trigger fallback
        self.assertTrue(self.scorer.should_fallback(question, bad_response))
    
    def test_cache_functionality(self):
        """Test embedding cache functionality"""
        if not self.scorer.is_available():
            self.skipTest("sentence-transformers not available")
        
        # Clear cache first
        self.scorer.clear_cache()
        
        # Get embedding (should cache it)
        text = "test text for caching"
        embedding1 = self.scorer.get_embedding(text)
        self.assertIsNotNone(embedding1)
        
        # Get same embedding again (should use cache)
        embedding2 = self.scorer.get_embedding(text)
        self.assertIsNotNone(embedding2)
        
        # Should be the same object from cache
        import numpy as np
        np.testing.assert_array_equal(embedding1, embedding2)
        
        # Check cache statistics
        stats = self.scorer.get_stats()
        self.assertGreater(stats['cache_hits'], 0)
        self.assertGreater(stats['cache_misses'], 0)
    
    def test_cache_lru_eviction(self):
        """Test LRU cache eviction behavior"""
        if not self.scorer.is_available():
            self.skipTest("sentence-transformers not available")
        
        # Use a small cache size for testing
        original_cache_size = self.scorer.config.SEMANTIC_CACHE_SIZE
        self.scorer.config.SEMANTIC_CACHE_SIZE = 3
        
        try:
            # Clear cache first
            self.scorer.clear_cache()
            
            # Fill cache to capacity
            texts = ["text one", "text two", "text three"]
            for text in texts:
                self.scorer.get_embedding(text)
            
            # Cache should be full
            self.assertEqual(len(self.scorer.embedding_cache), 3)
            
            # Add one more item - should evict oldest
            self.scorer.get_embedding("text four")
            self.assertEqual(len(self.scorer.embedding_cache), 3)
            
            # First item should be evicted
            self.assertNotIn("text one", self.scorer.embedding_cache)
            self.assertIn("text four", self.scorer.embedding_cache)
            
            # Access second item to make it recently used
            self.scorer.get_embedding("text two")
            
            # Add another item - should evict "text three" (oldest unused)
            self.scorer.get_embedding("text five")
            self.assertNotIn("text three", self.scorer.embedding_cache)
            self.assertIn("text two", self.scorer.embedding_cache)  # Should still be there
            
        finally:
            # Restore original cache size
            self.scorer.config.SEMANTIC_CACHE_SIZE = original_cache_size
    
    def test_stats_collection(self):
        """Test statistics collection"""
        stats = self.scorer.get_stats()
        
        self.assertIn('available', stats)
        self.assertIn('model_loaded', stats)
        self.assertIn('cache_size', stats)
        self.assertIn('cache_limit', stats)
        
        if self.scorer.is_available():
            self.assertTrue(stats['available'])
            self.assertTrue(stats['model_loaded'])
        else:
            self.assertFalse(stats['available'])


class TestLLMHandlerSemanticIntegration(unittest.TestCase):
    """Test semantic similarity integration with LLM handler"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = MockConfig()
        
        # Mock the OpenAI clients to avoid actual API calls
        with patch('llm_handler.OpenAI'), \
             patch('llm_handler.OpenAIRateLimiter'):
            self.handler = LLMHandler(self.config)
    
    def test_semantic_fallback_tracking(self):
        """Test that semantic fallbacks are tracked"""
        # Mock semantic scorer to always trigger fallback
        with patch.object(self.handler.semantic_scorer, 'should_fallback', return_value=True):
            result = self.handler._is_fallback_response("test response", "test question")
            self.assertTrue(result)
    
    def test_performance_stats_include_semantic(self):
        """Test that performance stats include semantic information"""
        stats = self.handler.get_performance_stats()
        
        self.assertIn('overall', stats)
        self.assertIn('semantic_fallbacks', stats['overall'])
        
        if self.config.SEMANTIC_SIMILARITY_ENABLED:
            self.assertIn('semantic_similarity', stats)


class TestSemanticSimilarityConfiguration(unittest.TestCase):
    """Test semantic similarity configuration validation"""
    
    def test_valid_configuration(self):
        """Test valid configuration values"""
        config = MockConfig()
        config.SEMANTIC_SIMILARITY_MIN_THRESHOLD = 0.5
        config.SEMANTIC_SIMILARITY_WEIGHT = 0.3
        config.SEMANTIC_CONTEXT_WEIGHT = 0.2
        config.SEMANTIC_CACHE_SIZE = 50
        
        # Should not raise any exceptions
        scorer = SemanticSimilarityScorer(config)
        self.assertIsNotNone(scorer)
    
    def test_configuration_edge_cases(self):
        """Test configuration edge cases"""
        config = MockConfig()
        
        # Test minimum values
        config.SEMANTIC_SIMILARITY_MIN_THRESHOLD = 0.0
        config.SEMANTIC_SIMILARITY_WEIGHT = 0.0
        config.SEMANTIC_CONTEXT_WEIGHT = 0.0
        config.SEMANTIC_CACHE_SIZE = 0
        
        scorer = SemanticSimilarityScorer(config)
        self.assertIsNotNone(scorer)
        
        # Test maximum values
        config.SEMANTIC_SIMILARITY_MIN_THRESHOLD = 1.0
        config.SEMANTIC_SIMILARITY_WEIGHT = 1.0
        config.SEMANTIC_CONTEXT_WEIGHT = 1.0
        config.SEMANTIC_CACHE_SIZE = 1000
        
        scorer = SemanticSimilarityScorer(config)
        self.assertIsNotNone(scorer)


def run_basic_tests():
    """Run basic tests that don't require sentence-transformers"""
    print("Running basic semantic similarity tests...")
    
    # Test disabled functionality
    config = MockConfig(semantic_enabled=False)
    scorer = SemanticSimilarityScorer(config)
    
    assert not scorer.is_available()
    assert scorer.compute_similarity("hello", "world") == 0.0
    assert not scorer.should_fallback("hello", "world")
    
    print("✓ Basic tests passed")


def run_advanced_tests():
    """Run advanced tests that require sentence-transformers"""
    print("Running advanced semantic similarity tests...")
    
    config = MockConfig(semantic_enabled=True)
    scorer = SemanticSimilarityScorer(config)
    
    if not scorer.is_available():
        print("⚠ sentence-transformers not available, skipping advanced tests")
        return
    
    # Test similarity computation
    similar_score = scorer.compute_similarity("Python programming", "Python coding")
    different_score = scorer.compute_similarity("Python programming", "cooking recipes")
    
    assert similar_score > different_score
    assert similar_score > 0.3
    assert different_score < 0.3
    
    # Test entity boost
    boost = scorer._compute_entity_boost("Python function", "def function_name():")
    assert boost > 1.0
    
    print("✓ Advanced tests passed")


if __name__ == "__main__":
    print("Testing semantic similarity functionality...")
    
    try:
        run_basic_tests()
        run_advanced_tests()
        print("\n✅ All semantic similarity tests passed!")
        
        # Run unittest suite if available
        if len(sys.argv) > 1 and sys.argv[1] == '--unittest':
            unittest.main(argv=[''])
            
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        sys.exit(1)