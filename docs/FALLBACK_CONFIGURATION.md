# LLM Fallback Configuration Guide

This guide explains how to configure the enhanced LLM fallback logic in AircBot. The fallback system determines when the bot should switch from a local LLM to a remote LLM (like OpenAI) based on response quality.

## Overview

The fallback system analyzes local LLM responses using multiple criteria:

1. **Response Length** - Detects very short or incomplete responses
2. **"I Don't Know" Patterns** - Identifies when the local LLM admits uncertainty
3. **Relevance Scoring** - Checks if responses match the question topic
4. **Semantic Coherence** - Detects repetitive or broken responses
5. **Response Type Matching** - Ensures responses match question types (code, explanations, etc.)

## Configuration Variables

All fallback settings are configurable via environment variables. Here are the available settings with their default values and explanations:

### Basic Response Filtering

#### `FALLBACK_MIN_RESPONSE_LENGTH` (default: `3`)
**What it does:** Minimum number of characters required before considering a response valid.
**Effect of changing:**
- **Lower values (1-2):** More permissive, accepts single-letter responses
- **Higher values (5-10):** More strict, requires longer responses
- **Recommended:** 3-5 for IRC environments, 5-10 for formal environments

```bash
# Very permissive - accepts "Y", "N", "OK"
export FALLBACK_MIN_RESPONSE_LENGTH=1

# Strict - requires at least 10 characters
export FALLBACK_MIN_RESPONSE_LENGTH=10
```

#### `FALLBACK_DONT_KNOW_CONTEXT_MIN_WORDS` (default: `15`)
**What it does:** Minimum word count for responses containing "I don't know" patterns before checking for additional context.
**Effect of changing:**
- **Lower values (5-10):** More likely to fallback on uncertain responses
- **Higher values (20-30):** More forgiving of uncertain responses that provide context
- **Recommended:** 10-15 for technical discussions, 15-25 for general chat

```bash
# Fallback quickly on uncertainty
export FALLBACK_DONT_KNOW_CONTEXT_MIN_WORDS=10

# Be more forgiving of uncertain but helpful responses
export FALLBACK_DONT_KNOW_CONTEXT_MIN_WORDS=25
```

### Relevance Scoring

#### `FALLBACK_RELEVANCE_MIN_RATIO` (default: `0.05`)
**What it does:** Minimum ratio of question keywords that must appear in the response.
**Effect of changing:**
- **Lower values (0.01-0.03):** More permissive, accepts responses with few matching keywords
- **Higher values (0.1-0.3):** More strict, requires more keyword overlap
- **Recommended:** 0.05-0.1 for technical discussions, 0.1-0.2 for structured Q&A

```bash
# Very permissive keyword matching
export FALLBACK_RELEVANCE_MIN_RATIO=0.01

# Strict keyword matching
export FALLBACK_RELEVANCE_MIN_RATIO=0.2
```

#### `FALLBACK_RELEVANCE_MIN_QUESTION_WORDS` (default: `3`)
**What it does:** Minimum number of meaningful words in a question before applying relevance scoring.
**Effect of changing:**
- **Lower values (1-2):** Apply relevance scoring to very short questions
- **Higher values (5-8):** Only apply relevance scoring to longer questions
- **Recommended:** 3-5 for most environments

### Question Type Matching

#### `FALLBACK_TYPE_MISMATCH_MIN_RATIO` (default: `0.1`)
**What it does:** Minimum keyword overlap required when response type doesn't match question type.
**Effect of changing:**
- **Lower values (0.05):** More forgiving of type mismatches
- **Higher values (0.3):** Stricter type matching requirements
- **Recommended:** 0.1-0.2 for balanced operation

#### `FALLBACK_TYPE_MISMATCH_MIN_QUESTION_WORDS` (default: `5`)
**What it does:** Minimum question length before applying type mismatch penalties.
**Effect of changing:**
- **Lower values (3-4):** Apply type checking to shorter questions
- **Higher values (7-10):** Only apply type checking to longer questions
- **Recommended:** 5-7 for most environments

### Response Quality Thresholds

#### `FALLBACK_GENERIC_RESPONSE_MAX_WORDS` (default: `25`)
**What it does:** Maximum word count for responses that start with generic phrases.
**Effect of changing:**
- **Lower values (10-15):** More aggressive at catching generic responses
- **Higher values (30-50):** More forgiving of responses that start generically but provide value
- **Recommended:** 20-30 for balanced operation

#### `FALLBACK_REPETITION_MAX_WORD_RATIO` (default: `0.3`)
**What it does:** Maximum ratio of any single word's occurrence in a response.
**Effect of changing:**
- **Lower values (0.2):** More aggressive at catching repetitive responses
- **Higher values (0.5):** More forgiving of repetitive but valid responses
- **Recommended:** 0.3-0.4 for most environments

#### `FALLBACK_REPETITION_MIN_WORD_LENGTH` (default: `3`)
**What it does:** Minimum word length to consider when detecting repetition.
**Effect of changing:**
- **Lower values (2):** Check repetition of shorter words like "is", "of"
- **Higher values (4-5):** Only check repetition of longer, more meaningful words
- **Recommended:** 3-4 for most environments

### Question Type Specific Settings

#### `FALLBACK_EXPLANATION_MIN_WORDS` (default: `8`)
**What it does:** Minimum word count for responses to explanation-type questions.
**Effect of changing:**
- **Lower values (5-6):** Accept shorter explanations
- **Higher values (12-20):** Require more detailed explanations
- **Recommended:** 8-12 for technical topics, 5-8 for simple questions

#### `FALLBACK_PROCEDURAL_SHORT_ANSWER_MAX_WORDS` (default: `15`)
**What it does:** Maximum word count for short procedural responses (bypasses detailed step requirements).
**Effect of changing:**
- **Lower values (10):** Require more detailed procedural responses
- **Higher values (25):** Accept longer responses without step-by-step format
- **Recommended:** 10-20 for most environments

#### `FALLBACK_CODE_SHORT_ANSWER_MAX_WORDS` (default: `10`)
**What it does:** Maximum word count for short code responses (bypasses code format requirements).
**Effect of changing:**
- **Lower values (5):** Require more detailed code responses
- **Higher values (20):** Accept longer responses without code format
- **Recommended:** 5-15 for most environments

## Common Configuration Scenarios

### Scenario 1: Permissive IRC Environment
For casual IRC channels where short responses are common:

```bash
export FALLBACK_MIN_RESPONSE_LENGTH=2
export FALLBACK_RELEVANCE_MIN_RATIO=0.03
export FALLBACK_DONT_KNOW_CONTEXT_MIN_WORDS=10
export FALLBACK_GENERIC_RESPONSE_MAX_WORDS=20
export FALLBACK_EXPLANATION_MIN_WORDS=5
```

### Scenario 2: Technical Support Environment
For technical support channels requiring detailed responses:

```bash
export FALLBACK_MIN_RESPONSE_LENGTH=5
export FALLBACK_RELEVANCE_MIN_RATIO=0.1
export FALLBACK_DONT_KNOW_CONTEXT_MIN_WORDS=20
export FALLBACK_GENERIC_RESPONSE_MAX_WORDS=30
export FALLBACK_EXPLANATION_MIN_WORDS=12
export FALLBACK_CODE_SHORT_ANSWER_MAX_WORDS=15
```

### Scenario 3: Strict Educational Environment
For educational environments requiring comprehensive responses:

```bash
export FALLBACK_MIN_RESPONSE_LENGTH=10
export FALLBACK_RELEVANCE_MIN_RATIO=0.15
export FALLBACK_DONT_KNOW_CONTEXT_MIN_WORDS=25
export FALLBACK_GENERIC_RESPONSE_MAX_WORDS=35
export FALLBACK_EXPLANATION_MIN_WORDS=15
export FALLBACK_REPETITION_MAX_WORD_RATIO=0.25
```

### Scenario 4: Development/Testing Environment
For development where you want to see more fallback behavior:

```bash
export FALLBACK_MIN_RESPONSE_LENGTH=5
export FALLBACK_RELEVANCE_MIN_RATIO=0.2
export FALLBACK_DONT_KNOW_CONTEXT_MIN_WORDS=30
export FALLBACK_GENERIC_RESPONSE_MAX_WORDS=40
export FALLBACK_EXPLANATION_MIN_WORDS=20
export FALLBACK_REPETITION_MAX_WORD_RATIO=0.2
```

## Testing Your Configuration

Use the provided test suite to validate your configuration:

```bash
# Run the fallback logic tests
python tests/test_fallback_logic.py

# Run with your custom configuration
FALLBACK_MIN_RESPONSE_LENGTH=5 python tests/test_fallback_logic.py
```

## Monitoring and Tuning

### Key Metrics to Monitor

1. **Fallback Rate**: Percentage of responses that trigger fallback
   - Target: 10-20% in normal operation
   - Too high (>30%): Configuration may be too strict
   - Too low (<5%): Configuration may be too permissive

2. **Response Quality**: User satisfaction with responses
   - Monitor user feedback and complaints
   - Track response relevance and completeness

3. **Cost Impact**: OpenAI API usage from fallbacks
   - Monitor API costs and request volume
   - Balance quality vs. cost based on your budget

### Configuration Tuning Process

1. **Start with defaults** and monitor for 1-2 weeks
2. **Identify problem areas** (too many/few fallbacks)
3. **Adjust one parameter at a time**
4. **Test with the test suite** before deploying
5. **Monitor results** for another week
6. **Repeat** until satisfied

### Common Issues and Solutions

#### Too Many Fallbacks
- Increase `FALLBACK_MIN_RESPONSE_LENGTH` (lower the threshold)
- Decrease `FALLBACK_RELEVANCE_MIN_RATIO` (be more permissive)
- Increase `FALLBACK_GENERIC_RESPONSE_MAX_WORDS` (accept longer generic responses)
- Decrease `FALLBACK_EXPLANATION_MIN_WORDS` (accept shorter explanations)

#### Too Few Fallbacks (Poor Quality Responses)
- Decrease `FALLBACK_MIN_RESPONSE_LENGTH` (raise the threshold)
- Increase `FALLBACK_RELEVANCE_MIN_RATIO` (be more strict)
- Decrease `FALLBACK_GENERIC_RESPONSE_MAX_WORDS` (reject generic responses faster)
- Increase `FALLBACK_EXPLANATION_MIN_WORDS` (require more detailed explanations)

#### Domain-Specific Issues
- For **code-heavy environments**: Increase `FALLBACK_CODE_SHORT_ANSWER_MAX_WORDS`
- For **procedure-heavy environments**: Increase `FALLBACK_PROCEDURAL_SHORT_ANSWER_MAX_WORDS`
- For **casual chat**: Decrease most thresholds to be more permissive
- For **formal discussions**: Increase most thresholds to be more strict

## Best Practices

1. **Start conservative** with default values
2. **Change one setting at a time** to understand impact
3. **Test thoroughly** with the test suite
4. **Monitor continuously** after deployment
5. **Document your changes** and reasoning
6. **Regular reviews** of effectiveness (monthly/quarterly)

## Troubleshooting

### Configuration Not Taking Effect
- Ensure environment variables are set before starting the bot
- Check that variable names are spelled correctly
- Verify values are within expected ranges (no negative numbers)

### Unexpected Behavior
- Enable debug logging to see fallback decisions
- Use the test suite to validate specific scenarios
- Check for typos in environment variable names

### Performance Issues
- Very low thresholds may cause excessive processing
- Consider impact on response time vs. quality trade-offs
- Monitor system resource usage

## Advanced Configuration

For advanced users, consider:

1. **Dynamic thresholds** based on time of day or channel activity
2. **User-specific configurations** for different user groups
3. **Topic-specific configurations** for different discussion areas
4. **A/B testing** different configurations for optimization

Remember that the goal is to balance response quality, cost, and user experience. The "perfect" configuration depends on your specific use case and user expectations.