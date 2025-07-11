import logging
import time
from typing import Optional, List, Dict, Any
import numpy as np
from functools import lru_cache
import threading
import re
from collections import OrderedDict

logger = logging.getLogger(__name__)

class SemanticSimilarityScorer:
    """
    Semantic similarity scorer for evaluating LLM response quality.
    Uses sentence-transformers to compute embeddings and similarity scores.
    """
    
    def __init__(self, config):
        self.config = config
        self.model = None
        self.embedding_cache = OrderedDict()  # Use OrderedDict for LRU behavior
        self.cache_lock = threading.Lock()
        self.model_loaded = False
        self.load_error = None
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Only initialize if semantic similarity is enabled
        if config.SEMANTIC_SIMILARITY_ENABLED:
            self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the sentence transformer model"""
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"Loading semantic similarity model: {self.config.SEMANTIC_MODEL_NAME}")
            start_time = time.time()
            
            # Load model with specified device
            self.model = SentenceTransformer(
                self.config.SEMANTIC_MODEL_NAME,
                device=self.config.SEMANTIC_MODEL_DEVICE
            )
            
            load_time = time.time() - start_time
            logger.info(f"Semantic similarity model loaded in {load_time:.2f}s")
            self.model_loaded = True
            
        except ImportError as e:
            self.load_error = f"sentence-transformers not installed: {e}"
            logger.error(self.load_error)
        except Exception as e:
            self.load_error = f"Failed to load semantic similarity model: {e}"
            logger.error(self.load_error)
    
    def is_available(self) -> bool:
        """Check if semantic similarity scoring is available"""
        return self.config.SEMANTIC_SIMILARITY_ENABLED and self.model_loaded and self.model is not None
    
    def get_embedding(self, text: str, use_cache: bool = True) -> Optional[np.ndarray]:
        """
        Get embedding for text with caching support
        
        Args:
            text: Input text to embed
            use_cache: Whether to use/update cache
            
        Returns:
            Embedding vector or None if unavailable
        """
        if not self.is_available():
            return None
            
        text_key = text.strip().lower()
        
        # Check cache first
        if use_cache:
            with self.cache_lock:
                if text_key in self.embedding_cache:
                    # Move to end (most recently used)
                    self.embedding_cache.move_to_end(text_key)
                    self.cache_hits += 1
                    return self.embedding_cache[text_key]
        
        try:
            # Generate embedding
            embedding = self.model.encode([text], convert_to_numpy=True)[0]
            self.cache_misses += 1
            
            # Cache if enabled with LRU eviction
            if use_cache:
                with self.cache_lock:
                    # If at capacity, remove oldest (least recently used) item
                    if len(self.embedding_cache) >= self.config.SEMANTIC_CACHE_SIZE:
                        self.embedding_cache.popitem(last=False)  # Remove first (oldest) item
                    
                    # Add new embedding (will be at the end, most recently used)
                    self.embedding_cache[text_key] = embedding
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute cosine similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1, or 0 if unavailable
        """
        if not self.is_available():
            return 0.0
            
        embedding1 = self.get_embedding(text1)
        embedding2 = self.get_embedding(text2)
        
        if embedding1 is None or embedding2 is None:
            return 0.0
        
        try:
            # Compute cosine similarity
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            similarity = dot_product / (norm1 * norm2)
            
            # Ensure similarity is between 0 and 1
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.error(f"Error computing similarity: {e}")
            return 0.0
    
    def score_response_relevance(self, question: str, response: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Score how relevant a response is to the question using semantic similarity
        
        Args:
            question: The original question
            response: The LLM response
            context: Optional conversation context
            
        Returns:
            Dictionary with relevance scores and metadata
        """
        if not self.is_available():
            return {
                'semantic_similarity': 0.0,
                'context_similarity': 0.0,
                'entity_boost': 1.0,
                'combined_score': 0.0,
                'available': False,
                'error': self.load_error
            }
        
        try:
            # Basic semantic similarity
            semantic_score = self.compute_similarity(question, response)
            
            # Context-aware scoring if enabled and context available
            context_score = 0.0
            if self.config.SEMANTIC_CONTEXT_ENABLED and context:
                context_score = self.compute_similarity(context, response)
            
            # Entity/keyword boosting
            entity_boost = self._compute_entity_boost(question, response)
            
            # Combined weighted score
            combined_score = (
                semantic_score * self.config.SEMANTIC_SIMILARITY_WEIGHT +
                context_score * self.config.SEMANTIC_CONTEXT_WEIGHT
            ) * entity_boost
            
            return {
                'semantic_similarity': semantic_score,
                'context_similarity': context_score,
                'entity_boost': entity_boost,
                'combined_score': combined_score,
                'available': True,
                'passes_threshold': combined_score >= self.config.SEMANTIC_SIMILARITY_MIN_THRESHOLD
            }
            
        except Exception as e:
            logger.error(f"Error scoring response relevance: {e}")
            return {
                'semantic_similarity': 0.0,
                'context_similarity': 0.0,
                'entity_boost': 1.0,
                'combined_score': 0.0,
                'available': False,
                'error': str(e)
            }
    
    def _compute_entity_boost(self, question: str, response: str) -> float:
        """
        Compute entity/keyword boost factor for technical terms
        
        Args:
            question: The original question
            response: The LLM response
            
        Returns:
            Boost factor (typically 1.0 to SEMANTIC_ENTITY_BOOST)
        """
        if not self.config.SEMANTIC_TECHNICAL_KEYWORDS:
            return 1.0
        
        # Extract technical terms from question
        question_lower = question.lower()
        response_lower = response.lower()
        
        # Count technical keywords in question
        question_tech_count = sum(1 for keyword in self.config.SEMANTIC_TECHNICAL_KEYWORDS 
                                 if keyword.lower() in question_lower)
        
        if question_tech_count == 0:
            return 1.0
        
        # Count technical keywords addressed in response
        response_tech_count = sum(1 for keyword in self.config.SEMANTIC_TECHNICAL_KEYWORDS 
                                 if keyword.lower() in response_lower)
        
        # Calculate boost based on technical term coverage
        if response_tech_count > 0:
            coverage_ratio = min(1.0, response_tech_count / question_tech_count)
            boost = 1.0 + (self.config.SEMANTIC_ENTITY_BOOST - 1.0) * coverage_ratio
            return boost
        
        return 1.0
    
    def should_fallback(self, question: str, response: str, context: Optional[str] = None) -> bool:
        """
        Determine if response should trigger fallback based on semantic similarity
        
        Args:
            question: The original question
            response: The LLM response
            context: Optional conversation context
            
        Returns:
            True if should fallback, False otherwise
        """
        if not self.is_available():
            return False  # Don't fallback if semantic similarity is unavailable
        
        scores = self.score_response_relevance(question, response, context)
        
        # Fallback if combined score is below threshold
        return not scores.get('passes_threshold', False)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get semantic similarity scoring statistics
        
        Returns:
            Dictionary with statistics
        """
        with self.cache_lock:
            cache_size = len(self.embedding_cache)
        
        # Calculate cache hit rate
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0.0
        
        return {
            'available': self.is_available(),
            'model_loaded': self.model_loaded,
            'model_name': self.config.SEMANTIC_MODEL_NAME,
            'device': self.config.SEMANTIC_MODEL_DEVICE,
            'cache_size': cache_size,
            'cache_limit': self.config.SEMANTIC_CACHE_SIZE,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': f"{hit_rate:.1f}%",
            'load_error': self.load_error
        }
    
    def clear_cache(self):
        """Clear the embedding cache and reset statistics"""
        with self.cache_lock:
            self.embedding_cache.clear()
            self.cache_hits = 0
            self.cache_misses = 0
        logger.info("Semantic similarity embedding cache cleared")