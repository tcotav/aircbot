import logging
import sqlite3
from openai import OpenAI
from typing import Optional, Dict, Any
import asyncio
from threading import Thread
import time
from prompts import get_system_prompt, get_error_message, get_name_response
from openai_rate_limiter import OpenAIRateLimiter

logger = logging.getLogger(__name__)

class LLMHandler:
    def __init__(self, config):
        self.config = config
        self.mode = config.LLM_MODE  # 'local_only', 'openai_only', 'fallback'
        
        # Clients
        self.local_client = None
        self.openai_client = None
        
        # OpenAI rate limiter
        self.openai_rate_limiter = None
        
        # Performance tracking
        self.response_times = {'local': [], 'openai': []}
        self.total_requests = {'local': 0, 'openai': 0}
        self.failed_requests = {'local': 0, 'openai': 0}
        
        # Initialize clients based on mode and configuration
        self._initialize_clients()
        
    def _initialize_clients(self):
        """Initialize the appropriate LLM clients based on configuration"""
        
        # Initialize local client (Ollama) if needed
        if self.mode in ['local_only', 'fallback'] and self.config.LLM_ENABLED:
            try:
                self.local_client = OpenAI(
                    base_url=self.config.LLM_BASE_URL,
                    api_key=self.config.LLM_API_KEY
                )
                logger.info(f"Local LLM initialized - Base URL: {self.config.LLM_BASE_URL}, Model: {self.config.LLM_MODEL}")
                self._test_connection('local')
            except Exception as e:
                logger.error(f"Failed to initialize local LLM client: {e}")
                
        # Initialize OpenAI client if needed
        if self.mode in ['openai_only', 'fallback'] and self.config.OPENAI_ENABLED:
            if not self.config.OPENAI_API_KEY:
                logger.error("OpenAI API key is required but not provided")
                return
                
            try:
                self.openai_client = OpenAI(api_key=self.config.OPENAI_API_KEY)
                logger.info(f"OpenAI client initialized - Model: {self.config.OPENAI_MODEL}")
                
                # Initialize OpenAI rate limiter
                self.openai_rate_limiter = OpenAIRateLimiter(self.config)
                
                self._test_connection('openai')
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                
        if not self.is_enabled():
            logger.warning(f"No LLM clients available with mode '{self.mode}'")
    
    def _test_connection(self, client_type: str):
        """Test the connection to the specified LLM client"""
        start_time = time.time()
        try:
            if client_type == 'local' and self.local_client:
                response = self.local_client.chat.completions.create(
                    model=self.config.LLM_MODEL,
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=10,
                    temperature=0.1
                )
            elif client_type == 'openai' and self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=self.config.OPENAI_MODEL,
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=10,
                    temperature=0.1
                )
            else:
                logger.warning(f"Cannot test {client_type} client - not initialized")
                return
                
            connection_time = time.time() - start_time
            logger.info(f"{client_type.title()} LLM connection test successful in {connection_time:.2f}s")
        except Exception as e:
            connection_time = time.time() - start_time
            logger.warning(f"{client_type.title()} LLM connection test failed after {connection_time:.2f}s: {e}")
    
    def is_enabled(self) -> bool:
        """Check if any LLM is enabled and available"""
        if self.mode == 'local_only':
            return self.local_client is not None
        elif self.mode == 'openai_only':
            return self.openai_client is not None
        elif self.mode == 'fallback':
            return self.local_client is not None or self.openai_client is not None
        return False
    
    
    def _check_for_name_question(self, question: str) -> Optional[str]:
        """
        Check if the user is asking about the bot's name and respond with IRC nickname
        
        Args:
            question: The user's question
            
        Returns:
            Name response if applicable, None otherwise
        """
        question_lower = question.lower().strip()
        
        name_patterns = [
            "what's your name",
            "what is your name", 
            "whats your name",
            "your name",
            "who are you",
            "what are you called",
            "what do i call you",
            "tell me your name",
        ]
        
        for pattern in name_patterns:
            if pattern in question_lower:
                return get_name_response(self.config.IRC_NICKNAME)
        
        return None

    def ask_llm(self, question: str, context: Optional[str] = None) -> Optional[str]:
        """
        Ask a question to the LLM based on the configured mode
        
        Args:
            question: The user's question
            context: Optional context from recent channel messages
            
        Returns:
            LLM response or error message
        """
        if not self.is_enabled():
            return get_error_message('llm_unavailable')
        
        # Check if this is a name question first
        name_response = self._check_for_name_question(question)
        if name_response:
            return name_response
        
        # Route based on mode
        if self.mode == 'openai_only':
            return self._ask_openai(question, context)
        elif self.mode == 'local_only':
            return self._ask_local(question, context)
        elif self.mode == 'fallback':
            return self._ask_fallback(question, context)
        else:
            logger.error(f"Unknown LLM mode: {self.mode}")
            return get_error_message('llm_error', f"Unknown mode: {self.mode}")
    
    def _ask_local(self, question: str, context: Optional[str] = None) -> Optional[str]:
        """Ask the local LLM (Ollama) with retry logic"""
        if not self.local_client:
            return get_error_message('llm_unavailable')
            
        for attempt in range(self.config.LLM_RETRY_ATTEMPTS):
            is_retry = attempt > 0
            if is_retry:
                logger.info(f"Retrying local LLM request (attempt {attempt + 1}/{self.config.LLM_RETRY_ATTEMPTS})")
            
            result = self._make_llm_request('local', question, context, is_retry)
            
            if result is None:  # Empty response - retry
                continue
            
            return result
        
        logger.warning(f"Local LLM request failed after {self.config.LLM_RETRY_ATTEMPTS} attempts")
        return get_error_message('no_response')
    
    def _ask_openai(self, question: str, context: Optional[str] = None) -> Optional[str]:
        """Ask OpenAI API"""
        if not self.openai_client:
            return get_error_message('llm_unavailable')
        
        # Check daily rate limit for OpenAI
        if self.openai_rate_limiter and not self.openai_rate_limiter.can_make_request():
            usage_stats = self.openai_rate_limiter.get_usage_stats()
            logger.warning(f"OpenAI daily limit reached: {usage_stats['today_usage']}/{usage_stats['daily_limit']}")
            return get_error_message('openai_limit_reached')
            
        # OpenAI is generally more reliable, so fewer retries
        for attempt in range(2):  # Max 2 attempts for OpenAI
            is_retry = attempt > 0
            if is_retry:
                logger.info(f"Retrying OpenAI request (attempt {attempt + 1}/2)")
            
            result = self._make_llm_request('openai', question, context, is_retry)
            
            if result is None:  # Empty response - retry
                continue
            
            # Record the successful request for rate limiting (only on success)
            if self.openai_rate_limiter and not result.startswith("❌") and not result.startswith("Error"):
                self.openai_rate_limiter.record_request()
            
            return result
        
        logger.warning("OpenAI request failed after 2 attempts")
        return get_error_message('no_response')
    
    def _ask_fallback(self, question: str, context: Optional[str] = None) -> Optional[str]:
        """Try local first, then fall back to OpenAI if local fails or gives poor response"""
        
        # Try local first if available
        if self.local_client:
            logger.info("Trying local LLM first (fallback mode)")
            local_result = self._ask_local(question, context)
            
            # Check if local response is good enough
            if local_result and not self._is_fallback_response(local_result):
                logger.info("Local LLM provided satisfactory response")
                return local_result
            else:
                logger.info("Local LLM response inadequate, falling back to OpenAI")
        
        # Fall back to OpenAI if available
        if self.openai_client:
            logger.info("Using OpenAI as fallback")
            return self._ask_openai(question, context)
        
        # If we get here, both failed or neither available
        if self.local_client:
            return local_result  # Return whatever local gave us
        else:
            return get_error_message('llm_unavailable')
    
    def _is_fallback_response(self, response: str) -> bool:
        """
        Determine if a response from local LLM warrants falling back to OpenAI
        
        Args:
            response: The response from local LLM
            
        Returns:
            True if we should fall back to OpenAI, False if response is adequate
        """
        if not response:
            return True
            
        # Check for error messages
        error_responses = [
            get_error_message('llm_unavailable'),
            get_error_message('no_response'),
            get_error_message('too_complex')
        ]
        
        if any(error in response for error in error_responses):
            return True
        
        # Check for very short or generic responses that might indicate the local model struggled
        if len(response.strip()) < 10:
            return True
            
        # Check for common "I don't know" patterns
        dont_know_patterns = [
            "i don't know",
            "i'm not sure",
            "i can't help",
            "i don't have information",
            "sorry, i don't",
            "i'm unable to",
            "i cannot provide"
        ]
        
        response_lower = response.lower()
        if any(pattern in response_lower for pattern in dont_know_patterns):
            return True
            
        return False

    def _make_llm_request(self, client_type: str, question: str, context: Optional[str] = None, is_retry: bool = False) -> Optional[str]:
        """
        Make a single LLM request to the specified client
        
        Args:
            client_type: 'local' or 'openai'
            question: The user's question
            context: Optional context from recent channel messages
            is_retry: Whether this is a retry attempt
            
        Returns:
            LLM response or None if empty (for retry), error message for other failures
        """
        # Start timing the LLM request
        start_time = time.time()
        
        try:
            # Select the appropriate client and settings
            if client_type == 'local':
                client = self.local_client
                model = self.config.LLM_MODEL
                max_tokens = self.config.LLM_MAX_TOKENS
                temperature = self.config.LLM_TEMPERATURE
            elif client_type == 'openai':
                client = self.openai_client
                model = self.config.OPENAI_MODEL
                max_tokens = self.config.OPENAI_MAX_TOKENS
                temperature = self.config.OPENAI_TEMPERATURE
            else:
                logger.error(f"Unknown client type: {client_type}")
                return get_error_message('llm_error', f"Unknown client type: {client_type}")
            
            if not client:
                logger.error(f"{client_type} client not available")
                return get_error_message('llm_unavailable')
            
            # Build the prompt
            messages = []
            
            system_content = get_system_prompt(self.config.IRC_NICKNAME, context)
            messages.append({
                "role": "system",
                "content": system_content
            })
            
            messages.append({
                "role": "user",
                "content": question
            })
            
            # Make the API call
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False
            )
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Get raw answer from LLM
            raw_answer = response.choices[0].message.content
            if not raw_answer or not raw_answer.strip():
                # Empty response from LLM - this should trigger a retry
                if is_retry:
                    logger.warning(f"{client_type} LLM returned empty response on retry after {response_time:.2f}s")
                else:
                    logger.warning(f"{client_type} LLM returned empty response after {response_time:.2f}s")
                self.failed_requests[client_type] += 1
                return None  # Return None to trigger retry
            
            answer = raw_answer.strip()
            
            # Validate response length and complexity
            validated_answer = self._validate_response_length(answer)
            
            # Check if validation failed (but this should NOT trigger retries)
            if validated_answer in [get_error_message('no_response'), get_error_message('too_complex')]:
                # Track performance statistics for failed validation
                self.total_requests[client_type] += 1
                self.response_times[client_type].append(response_time)
                # Keep only last 100 response times to avoid memory growth
                if len(self.response_times[client_type]) > 100:
                    self.response_times[client_type] = self.response_times[client_type][-100:]
                
                logger.info(f"{client_type} LLM query: '{question[:50]}...' -> validation failed ({validated_answer}), time: {response_time:.2f}s")
                return validated_answer  # Return error message directly
            
            # Track performance statistics for successful response
            self.total_requests[client_type] += 1
            self.response_times[client_type].append(response_time)
            # Keep only last 100 response times to avoid memory growth
            if len(self.response_times[client_type]) > 100:
                self.response_times[client_type] = self.response_times[client_type][-100:]
            
            # Log the interaction with timing information
            logger.info(f"{client_type} LLM query: '{question[:50]}...' -> response length: {len(validated_answer)} chars, time: {response_time:.2f}s")
            
            return validated_answer
            
        except Exception as e:
            # Calculate response time even for errors
            response_time = time.time() - start_time
            self.failed_requests[client_type] += 1
            logger.error(f"Error calling {client_type} LLM after {response_time:.2f}s: {e}")
            return get_error_message('llm_error', str(e))

    def get_performance_stats(self) -> dict:
        """
        Get performance statistics for all LLM clients
        
        Returns:
            Dictionary with performance metrics for each client type
        """
        stats = {}
        
        for client_type in ['local', 'openai']:
            response_times = self.response_times[client_type]
            total_requests = self.total_requests[client_type]
            failed_requests = self.failed_requests[client_type]
            
            if not response_times:
                stats[client_type] = {
                    'total_requests': total_requests,
                    'failed_requests': failed_requests,
                    'success_rate': 0.0,
                    'avg_response_time': 0.0,
                    'min_response_time': 0.0,
                    'max_response_time': 0.0,
                    'enabled': client_type == 'local' and self.local_client is not None or 
                              client_type == 'openai' and self.openai_client is not None
                }
            else:
                avg_time = sum(response_times) / len(response_times)
                success_rate = (total_requests / (total_requests + failed_requests)) * 100 if (total_requests + failed_requests) > 0 else 0.0
                
                stats[client_type] = {
                    'total_requests': total_requests,
                    'failed_requests': failed_requests,
                    'success_rate': f"{success_rate:.1f}%",
                    'avg_response_time': f"{avg_time:.2f}s",
                    'min_response_time': f"{min(response_times):.2f}s",
                    'max_response_time': f"{max(response_times):.2f}s",
                    'recent_requests': len(response_times),
                    'enabled': client_type == 'local' and self.local_client is not None or 
                              client_type == 'openai' and self.openai_client is not None
                }
        
        # Add OpenAI usage stats if available
        if self.openai_rate_limiter:
            openai_usage = self.openai_rate_limiter.get_usage_stats()
            stats['openai']['daily_usage'] = openai_usage['today_usage']
            stats['openai']['daily_limit'] = openai_usage['daily_limit']
            stats['openai']['daily_remaining'] = openai_usage['remaining']
        
        # Add mode information
        stats['mode'] = self.mode
        stats['overall'] = {
            'total_requests': sum(self.total_requests.values()),
            'total_failed': sum(self.failed_requests.values())
        }
        
        return stats
    
    def _validate_response_length(self, response: str) -> str:
        """
        Validate that response is appropriately short for IRC
        
        Args:
            response: Raw LLM response
            
        Returns:
            Original response if short enough, otherwise fallback message
        """
        import re
        
        # Aggressively remove ALL <think> content - both closed and unclosed tags
        # Remove everything from the first <think> to the last </think> (if it exists)
        clean_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        
        # If there's still an unclosed <think>, remove everything from that point onwards
        if '<think>' in clean_response:
            clean_response = clean_response.split('<think>')[0]
        
        # Remove any remaining think tag artifacts
        clean_response = re.sub(r'</?think[^>]*>', '', clean_response, flags=re.IGNORECASE)
        
        # Clean up whitespace
        clean_response = clean_response.strip()
        
        # If response is empty after cleaning, provide a friendly fallback
        if not clean_response:
            return get_error_message('no_response')
        
        # Count sentences (rough approximation) - but exclude numbered list items
        import re
        
        # Count periods, but exclude those that are part of numbered lists (e.g., "1.", "2.")
        # Look for periods that are NOT preceded by a digit
        period_count = len(re.findall(r'(?<!\d)\.', clean_response))
        sentence_endings = period_count + clean_response.count('!') + clean_response.count('?')
        
        # Be more lenient - allow up to 3 sentences and 400 chars for simple conversations
        if sentence_endings > 3 or len(clean_response) > 400:
            return get_error_message('too_complex')
        
        # Check for genuine complexity indicators that suggest technical explanations
        import re
        
        # Count numbered list items more accurately
        numbered_items = len(re.findall(r'\d+\.', clean_response))
        bullet_items = clean_response.count('•')
        
        complexity_indicators = [
            clean_response.count('\n') > 2,  # Multiple paragraphs (more lenient)
            numbered_items > 5 or bullet_items > 5,  # Long lists (more than 5 items)
            clean_response.count(':') > 3,  # Many explanations
            any(word in clean_response.lower() for word in ['however', 'furthermore', 'moreover', 'specifically', 'particularly']),  # Academic language
        ]
        
        if any(complexity_indicators):
            return get_error_message('too_complex')
        
        return clean_response
    
    def get_channel_context(self, db, channel: str, limit: int = 10) -> str:
        """
        Get recent channel messages for context
        
        Args:
            db: Database instance
            channel: Channel name
            limit: Number of recent messages to include
            
        Returns:
            Formatted context string
        """
        try:
            # Get recent messages from database
            with sqlite3.connect(db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT user, message, datetime(timestamp, 'localtime') as time
                    FROM messages 
                    WHERE channel = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (channel, limit))
                
                messages = cursor.fetchall()
                
                if not messages:
                    return ""
                
                # Format context (reverse to get chronological order)
                context_lines = []
                for msg in reversed(messages):
                    # Skip bot commands to avoid recursion
                    if not msg['message'].startswith('!'):
                        context_lines.append(f"[{msg['time']}] <{msg['user']}> {msg['message']}")
                
                return "\n".join(context_lines[-5:])  # Last 5 non-command messages
                
        except Exception as e:
            logger.error(f"Error getting channel context: {e}")
            return ""
