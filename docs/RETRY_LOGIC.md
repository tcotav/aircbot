# LLM Retry Logic Documentation

## Overview

The bot implements intelligent retry logic for LLM requests to handle empty responses gracefully while avoiding unnecessary retries for validation failures.

## How It Works

### Retry Triggers
The bot will retry LLM requests **only** when:
- The LLM returns a completely empty response (`""` or `None`)
- The LLM response is empty after stripping whitespace

### No Retry Scenarios
The bot will **NOT** retry when:
- Validation fails (response is too complex/long)
- API errors occur (network issues, authentication failures)
- The LLM returns content that gets rejected by validation logic

### Configuration

The retry behavior is controlled by the `LLM_RETRY_ATTEMPTS` setting:

```bash
# .env file
LLM_RETRY_ATTEMPTS=3  # Default: 3 attempts
```

This means:
- First attempt (not counted as retry)
- Up to 2 additional retry attempts if first returns empty
- Total maximum of 3 API calls per user request

## Implementation Details

### Flow Diagram

```
User asks question
     ↓
ask_llm() called
     ↓
Loop for attempts 1-3:
     ↓
_make_llm_request()
     ↓
Check raw LLM response:
     ├─ Empty? → Return None → Continue loop (retry)
     ├─ Success? → Validate → Return result → Exit loop
     └─ Error? → Return error message → Exit loop
     ↓
All retries exhausted?
     └─ Return "no response" error
```

### Key Methods

#### `ask_llm(question, context)`
- Main entry point for LLM requests
- Handles the retry loop
- Only retries on `None` returns from `_make_llm_request`

#### `_make_llm_request(question, context, is_retry)`
- Makes the actual API call
- Returns `None` for empty responses (triggers retry)
- Returns error messages for failures (no retry)
- Returns validated response for success (no retry)

### Performance Tracking

The retry logic properly tracks performance statistics:

- **Failed requests**: Incremented for each empty response and API error
- **Successful requests**: Incremented only for valid responses
- **Response times**: Tracked for all attempts (including failed retries)
- **Retry logging**: Each retry attempt is logged with attempt number

### Example Scenarios

#### Scenario 1: Empty Response with Successful Retry
```
Attempt 1: LLM returns "" → Failed request + 1, retry
Attempt 2: LLM returns "Hello!" → Successful request + 1, return result
Final: 1 failed, 1 successful, 2 total API calls
```

#### Scenario 2: Validation Failure (No Retry)
```
Attempt 1: LLM returns complex response → Validation fails → return error message
Final: 1 successful request (API succeeded), 1 total API call
```

#### Scenario 3: All Retries Exhausted
```
Attempt 1: LLM returns "" → Failed request + 1, retry
Attempt 2: LLM returns "" → Failed request + 1, retry  
Attempt 3: LLM returns "" → Failed request + 1, give up
Final: 3 failed, 0 successful, 3 total API calls, return "no response" error
```

## Monitoring

Use the `!performance` command to monitor retry effectiveness:

```
!performance
📊 LLM Performance Stats:
• Total requests: 25          # Successful responses
• Failed requests: 8          # Empty responses + API errors
• Success rate: 75.8%         # 25/(25+8) * 100
• Average response time: 1.2s # Including retry attempts
• Response time range: 0.5s - 3.2s
• Recent sample size: 25 requests
```

High failed request counts may indicate:
- LLM model issues (returning empty responses frequently)
- Network connectivity problems
- Model overload or timeout issues

## Testing

The retry logic is thoroughly tested in `test_simple_retry.py`:

- ✅ Empty responses trigger exactly the configured number of retries
- ✅ Validation failures do NOT trigger retries  
- ✅ Successful responses on first try require no retries
- ✅ Performance statistics are tracked correctly during retries
- ✅ Retry logging works as expected

Run tests with:
```bash
python test_simple_retry.py
```
