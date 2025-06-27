#!/usr/bin/env python3
"""
Rate limiting functionality for the IRC bot
"""

import time
import threading
from collections import defaultdict, deque
from typing import Dict, Deque
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter using sliding window approach"""
    
    def __init__(self, user_limit_per_minute: int = 1, total_limit_per_minute: int = 10):
        """
        Initialize rate limiter
        
        Args:
            user_limit_per_minute: Maximum requests per user per minute
            total_limit_per_minute: Maximum total requests per minute across all users
        """
        self.user_limit_per_minute = user_limit_per_minute
        self.total_limit_per_minute = total_limit_per_minute
        self.window_size = 60  # 1 minute in seconds
        
        # Track requests per user (sliding window)
        self.user_requests: Dict[str, Deque[float]] = defaultdict(deque)
        
        # Track total requests (sliding window)
        self.total_requests: Deque[float] = deque()
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
        logger.info(f"Rate limiter initialized: {user_limit_per_minute} per user/min, {total_limit_per_minute} total/min")
    
    def is_allowed(self, user: str) -> bool:
        """
        Check if a request from user is allowed
        
        Args:
            user: Username making the request
            
        Returns:
            True if request is allowed, False if rate limited
        """
        current_time = time.time()
        
        with self.lock:
            # Clean up old requests (older than window_size)
            self._cleanup_old_requests(current_time)
            
            # Check user-specific rate limit
            user_request_count = len(self.user_requests[user])
            if user_request_count >= self.user_limit_per_minute:
                logger.warning(f"Rate limit exceeded for user {user}: {user_request_count}/{self.user_limit_per_minute} per minute")
                return False
            
            # Check total rate limit
            total_request_count = len(self.total_requests)
            if total_request_count >= self.total_limit_per_minute:
                logger.warning(f"Total rate limit exceeded: {total_request_count}/{self.total_limit_per_minute} per minute")
                return False
            
            # Request is allowed - record it
            self.user_requests[user].append(current_time)
            self.total_requests.append(current_time)
            
            logger.debug(f"Request allowed for {user}. User: {user_request_count + 1}/{self.user_limit_per_minute}, Total: {total_request_count + 1}/{self.total_limit_per_minute}")
            return True
    
    def _cleanup_old_requests(self, current_time: float):
        """Remove requests older than the window size"""
        cutoff_time = current_time - self.window_size
        
        # Clean up user requests
        for user in list(self.user_requests.keys()):
            user_queue = self.user_requests[user]
            while user_queue and user_queue[0] < cutoff_time:
                user_queue.popleft()
            
            # Remove empty queues to save memory
            if not user_queue:
                del self.user_requests[user]
        
        # Clean up total requests
        while self.total_requests and self.total_requests[0] < cutoff_time:
            self.total_requests.popleft()
    
    def get_stats(self) -> Dict[str, int]:
        """Get current rate limiting statistics"""
        current_time = time.time()
        
        with self.lock:
            self._cleanup_old_requests(current_time)
            
            total_requests = len(self.total_requests)
            active_users = len(self.user_requests)
            
            return {
                'total_requests_this_minute': total_requests,
                'total_limit': self.total_limit_per_minute,
                'active_users': active_users,
                'user_limit': self.user_limit_per_minute
            }
    
    def get_user_stats(self, user: str) -> Dict[str, int]:
        """Get rate limiting statistics for a specific user"""
        current_time = time.time()
        
        with self.lock:
            self._cleanup_old_requests(current_time)
            
            user_requests = len(self.user_requests.get(user, []))
            
            return {
                'requests_this_minute': user_requests,
                'limit': self.user_limit_per_minute,
                'remaining': max(0, self.user_limit_per_minute - user_requests)
            }
