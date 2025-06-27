import logging
import sqlite3
from openai import OpenAI
from typing import Optional
import asyncio
from threading import Thread
import time

logger = logging.getLogger(__name__)

class LLMHandler:
    def __init__(self, config):
        self.config = config
        self.enabled = config.LLM_ENABLED
        self.client = None
        
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
        try:
            response = self.client.chat.completions.create(
                model=self.config.LLM_MODEL,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10,
                temperature=0.1
            )
            logger.info("LLM connection test successful")
        except Exception as e:
            logger.warning(f"LLM connection test failed: {e}")
            # Don't disable, just warn - might work later
    
    def is_enabled(self) -> bool:
        """Check if LLM is enabled and available"""
        return self.enabled and self.client is not None
    
    def ask_llm(self, question: str, context: Optional[str] = None) -> Optional[str]:
        """
        Ask a question to the LLM
        
        Args:
            question: The user's question
            context: Optional context from recent channel messages
            
        Returns:
            LLM response or None if error
        """
        if not self.is_enabled():
            return "❌ LLM is not available"
        
        try:
            # Build the prompt
            messages = []
            
            if context:
                messages.append({
                    "role": "system", 
                    "content": f"You are bubba, a friendly IRC bot. Recent context:\n{context}\n\nRespond immediately without explanation or reasoning. Example: User says 'hello' -> You say 'Hi there!' User says 'how are you?' -> You say 'I'm great, thanks!' Keep responses 1-2 sentences max."
                })
            else:
                messages.append({
                    "role": "system",
                    "content": "You are bubba, a friendly IRC bot. Respond immediately without explanation or reasoning. Example: User says 'hello' -> You say 'Hi there!' User says 'how are you?' -> You say 'I'm great, thanks!' Keep responses 1-2 sentences max."
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
            
            answer = response.choices[0].message.content.strip()
            
            # Validate response length and complexity
            validated_answer = self._validate_response_length(answer)
            
            # Log the interaction (without full context to avoid spam)
            logger.info(f"LLM query: '{question[:50]}...' -> response length: {len(validated_answer)} chars")
            
            return validated_answer
            
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return f"❌ Error calling LLM: {str(e)}"
    
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
            return "I'm not sure how to respond to that."
        
        # Count sentences (rough approximation)
        sentence_endings = clean_response.count('.') + clean_response.count('!') + clean_response.count('?')
        
        # Be more lenient - allow up to 3 sentences and 400 chars for simple conversations
        if sentence_endings > 3 or len(clean_response) > 400:
            return "That's too complicated to answer here"
        
        # Check for genuine complexity indicators that suggest technical explanations
        complexity_indicators = [
            clean_response.count('\n') > 2,  # Multiple paragraphs (more lenient)
            clean_response.count('1.') > 1 or clean_response.count('•') > 2,  # Long lists
            clean_response.count(':') > 3,  # Many explanations
            any(word in clean_response.lower() for word in ['however', 'furthermore', 'moreover', 'specifically', 'particularly']),  # Academic language
        ]
        
        if any(complexity_indicators):
            return "That's too complicated to answer here"
        
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
