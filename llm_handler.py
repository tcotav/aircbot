import logging
import sqlite3
from openai import OpenAI
from typing import Optional
import asyncio
from threading import Thread
import time
from prompts import get_system_prompt, get_error_message, get_name_response

logger = logging.getLogger(__name__)

class LLMHandler:
    def __init__(self, config):
        self.config = config
        self.enabled = config.LLM_ENABLED
        self.client = None
        
        # Performance tracking
        self.response_times = []
        self.total_requests = 0
        self.failed_requests = 0
        
        if self.enabled:
            try:
                # Initialize OpenAI client with Ollama settings
                self.client = OpenAI(
                    base_url=config.LLM_BASE_URL,
                    api_key=config.LLM_API_KEY
                )
                logger.info(f"LLM initialized - Base URL: {config.LLM_BASE_URL}, Model: {config.LLM_MODEL}")
                
                # Test connection
                self._test_connection()
                
            except Exception as e:
                logger.error(f"Failed to initialize LLM client: {e}")
                self.enabled = False
        else:
            logger.info("LLM integration disabled")
    
    def _test_connection(self):
        """Test the connection to the LLM"""
        start_time = time.time()
        try:
            response = self.client.chat.completions.create(
                model=self.config.LLM_MODEL,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10,
                temperature=0.1
            )
            connection_time = time.time() - start_time
            logger.info(f"LLM connection test successful in {connection_time:.2f}s")
        except Exception as e:
            connection_time = time.time() - start_time
            logger.warning(f"LLM connection test failed after {connection_time:.2f}s: {e}")
            # Don't disable, just warn - might work later
    
    def is_enabled(self) -> bool:
        """Check if LLM is enabled and available"""
        return self.enabled and self.client is not None
    
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
        Ask a question to the LLM with retry logic for empty responses
        
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
        
        # Attempt the request with retries for empty responses only
        for attempt in range(self.config.LLM_RETRY_ATTEMPTS):
            is_retry = attempt > 0
            if is_retry:
                logger.info(f"Retrying LLM request (attempt {attempt + 1}/{self.config.LLM_RETRY_ATTEMPTS}) for: '{question[:30]}...'")
            
            result = self._make_llm_request(question, context, is_retry)
            
            # If result is None, it means empty response - continue to retry
            if result is None:
                continue
            
            # If result is not None, it's either a success or a validation/error message
            # In either case, return it (don't retry on validation failures)
            return result
        
        # All retries exhausted due to empty responses
        logger.warning(f"LLM request failed after {self.config.LLM_RETRY_ATTEMPTS} attempts (empty responses) for: '{question[:30]}...'")
        return get_error_message('no_response')

    def _make_llm_request(self, question: str, context: Optional[str] = None, is_retry: bool = False) -> Optional[str]:
        """
        Make a single LLM request
        
        Args:
            question: The user's question
            context: Optional context from recent channel messages
            is_retry: Whether this is a retry attempt
            
        Returns:
            LLM response or None if empty (for retry), error message for other failures
        """
        # Start timing the LLM request
        start_time = time.time()
        
        try:
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
            response = self.client.chat.completions.create(
                model=self.config.LLM_MODEL,
                messages=messages,
                max_tokens=self.config.LLM_MAX_TOKENS,
                temperature=self.config.LLM_TEMPERATURE,
                stream=False
            )
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Get raw answer from LLM
            raw_answer = response.choices[0].message.content
            if not raw_answer or not raw_answer.strip():
                # Empty response from LLM - this should trigger a retry
                if is_retry:
                    logger.warning(f"LLM returned empty response on retry after {response_time:.2f}s")
                else:
                    logger.warning(f"LLM returned empty response after {response_time:.2f}s")
                self.failed_requests += 1
                return None  # Return None to trigger retry
            
            answer = raw_answer.strip()
            
            # Validate response length and complexity
            validated_answer = self._validate_response_length(answer)
            
            # Check if validation failed (but this should NOT trigger retries)
            if validated_answer in [get_error_message('no_response'), get_error_message('too_complex')]:
                # Track performance statistics for failed validation
                self.total_requests += 1
                self.response_times.append(response_time)
                # Keep only last 100 response times to avoid memory growth
                if len(self.response_times) > 100:
                    self.response_times = self.response_times[-100:]
                
                logger.info(f"LLM query: '{question[:50]}...' -> validation failed ({validated_answer}), time: {response_time:.2f}s")
                return validated_answer  # Return error message directly
            
            # Track performance statistics for successful response
            self.total_requests += 1
            self.response_times.append(response_time)
            # Keep only last 100 response times to avoid memory growth
            if len(self.response_times) > 100:
                self.response_times = self.response_times[-100:]
            
            # Log the interaction with timing information
            logger.info(f"LLM query: '{question[:50]}...' -> response length: {len(validated_answer)} chars, time: {response_time:.2f}s")
            
            return validated_answer
            
        except Exception as e:
            # Calculate response time even for errors
            response_time = time.time() - start_time
            self.failed_requests += 1
            logger.error(f"Error calling LLM after {response_time:.2f}s: {e}")
            return get_error_message('llm_error', str(e))

    def get_performance_stats(self) -> dict:
        """
        Get performance statistics for the LLM
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.response_times:
            return {
                'total_requests': self.total_requests,
                'failed_requests': self.failed_requests,
                'success_rate': 0.0,
                'avg_response_time': 0.0,
                'min_response_time': 0.0,
                'max_response_time': 0.0
            }
        
        avg_time = sum(self.response_times) / len(self.response_times)
        success_rate = (self.total_requests / (self.total_requests + self.failed_requests)) * 100 if (self.total_requests + self.failed_requests) > 0 else 0.0
        
        return {
            'total_requests': self.total_requests,
            'failed_requests': self.failed_requests,
            'success_rate': f"{success_rate:.1f}%",
            'avg_response_time': f"{avg_time:.2f}s",
            'min_response_time': f"{min(self.response_times):.2f}s",
            'max_response_time': f"{max(self.response_times):.2f}s",
            'recent_requests': len(self.response_times)
        }
    
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
