# IRC Bot Context Management Implementation

## Overview

We've successfully implemented intelligent context management for the IRC bot that addresses your original question: **"How will we decide if the previous N messages are relevant to the LLM request or not?"**

## Implementation Summary

### 1. **Configuration Options** (config.py)
Added new environment variables to control context behavior:
- `MESSAGE_QUEUE_SIZE=50` - Local message queue size per channel
- `CONTEXT_ANALYSIS_ENABLED=true` - Enable/disable intelligent context analysis
- `CONTEXT_RELEVANCE_THRESHOLD=0.3` - Relevance score threshold (0.0-1.0)
- `SAVE_MESSAGES_TO_DB=false` - Optional database storage for messages
- `MAX_CONTEXT_MESSAGES=10` - Maximum messages to include as context

#### **Configurable Relevance Scoring Weights:**
Fine-tune the relevance algorithm for your community:
- `WEIGHT_KEYWORD_OVERLAP=0.4` - Direct word matches between query and message
- `WEIGHT_TECHNICAL_KEYWORDS=0.3` - Bonus for programming/technical terms
- `WEIGHT_QUESTION_CONTEXT=0.15` - Bonus for questions and answers
- `WEIGHT_RECENCY_BONUS=0.1` - Slight preference for recent messages
- `WEIGHT_BOT_INTERACTION=0.1` - Boost for commands and bot mentions
- `WEIGHT_URL_BONUS=0.2` - Bonus for links when query is about resources
- `PENALTY_SHORT_MESSAGE=0.7` - Penalty multiplier for very short messages

### 2. **Context Manager** (context_manager.py)
New intelligent context management system with:

#### **Message Storage:**
- Local message queues per channel (configurable size)
- Message metadata: user, content, timestamp, is_command, is_bot_mention

#### **Relevance Detection Algorithm:**
The system uses a multi-factor scoring algorithm to determine relevance:

1. **Keyword Overlap (40% weight)** - Direct word matches between query and message
2. **Technical Keyword Bonus (30% weight)** - Programming/tech terms boost relevance
3. **Question Context (15% weight)** - Questions and answers are often related
4. **Recency Bonus (10% weight)** - Recent messages get slight preference
5. **Bot Interaction Bonus (10% weight)** - Commands and mentions are prioritized
6. **Additional factors:**
   - Length penalty for very short messages
   - URL/link bonus for resource-related queries

#### **Smart Context Selection:**
- Messages scoring above threshold are selected
- Sorted by relevance score, limited by max count
- Fallback to recent messages if no relevant context found
- Chronological ordering preserved in final context

### 3. **Bot Integration** (bot.py)
Enhanced the main bot with:

#### **Message Processing:**
- All messages automatically added to context queue
- Optional database storage (configurable)
- Metadata tracking (commands, mentions)

#### **Intelligent LLM Context:**
- Replaces simple "recent context" with smart relevance-based selection
- Formatted context for LLM with timestamps and indicators
- Graceful fallback to recent messages when no relevant context found

#### **New Commands:**
- `!context` - Show context summary for channel
- `!context clear` - Clear context queue
- `!context test <query>` - Test relevance detection

## How It Solves Your Original Problem

### **The Challenge:**
> "How will we decide if the previous N messages are relevant to the LLM request or not?"

### **Our Solution:**
1. **Multi-factor Relevance Scoring** - Uses keyword overlap, technical terms, question patterns, recency, and interaction type
2. **Configurable Thresholds** - Admins can tune sensitivity via `CONTEXT_RELEVANCE_THRESHOLD`
3. **Intelligent Selection** - Automatically picks most relevant messages up to configured limit
4. **Graceful Degradation** - Falls back to recent messages if no relevant context found

## Usage Examples

### **Environment Configuration:**
```bash
# Basic context settings
MESSAGE_QUEUE_SIZE=50
CONTEXT_ANALYSIS_ENABLED=true
CONTEXT_RELEVANCE_THRESHOLD=0.3
SAVE_MESSAGES_TO_DB=false
MAX_CONTEXT_MESSAGES=10

# Fine-tune relevance scoring for your community
WEIGHT_KEYWORD_OVERLAP=0.4
WEIGHT_TECHNICAL_KEYWORDS=0.3
WEIGHT_QUESTION_CONTEXT=0.15
WEIGHT_RECENCY_BONUS=0.1
WEIGHT_BOT_INTERACTION=0.1
WEIGHT_URL_BONUS=0.2
PENALTY_SHORT_MESSAGE=0.7
```

### **Weight Tuning Examples:**

**For Technical Communities (programming, DevOps):**
```bash
WEIGHT_TECHNICAL_KEYWORDS=0.5
WEIGHT_KEYWORD_OVERLAP=0.3
WEIGHT_QUESTION_CONTEXT=0.15
```

**For General Chat Communities:**
```bash
WEIGHT_KEYWORD_OVERLAP=0.5
WEIGHT_QUESTION_CONTEXT=0.2
WEIGHT_RECENCY_BONUS=0.15
```

**For Support Channels (Q&A focused):**
```bash
WEIGHT_QUESTION_CONTEXT=0.4
WEIGHT_BOT_INTERACTION=0.2
WEIGHT_KEYWORD_OVERLAP=0.3
```

### **Bot Commands:**
```
!context                          # Show context summary
!context clear                    # Clear message queue
!context test how to debug python # Test relevance for query
!ask how do I fix this error?     # Uses intelligent context
```

### **Automatic Context Detection:**
When a user asks "How do I fix AttributeError?", the system will:
1. Analyze all recent messages for relevance
2. Find messages containing keywords like "error", "Python", "AttributeError"
3. Prioritize technical discussions and bot interactions
4. Provide top relevant messages as context to the LLM

## Benefits

1. **Better AI Responses** - LLM gets relevant context instead of random recent messages
2. **Configurable Behavior** - Admins can tune for their community's needs
3. **Efficient Processing** - Local queues avoid database overhead for context
4. **Transparent Testing** - `!context test` command shows what context would be selected
5. **Graceful Fallback** - Always provides some context even if relevance detection fails

## Performance Considerations

- **Memory Usage:** Configurable queue size limits memory per channel
- **CPU Usage:** Relevance scoring is lightweight (regex + word matching)
- **Database Optional:** Context works entirely from memory, DB storage is optional
- **Thread Safety:** Context operations are atomic and thread-safe

## Future Enhancements

Potential improvements could include:
1. **Semantic similarity** using embeddings for better relevance detection
2. **User conversation threading** to track multi-user discussions
3. **Topic modeling** to identify conversation themes
4. **Learning from user feedback** to improve relevance scoring

The current implementation provides a solid foundation that intelligently selects relevant context while remaining configurable and performant!
