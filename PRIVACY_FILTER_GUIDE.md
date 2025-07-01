# Privacy Filter Implementation Guide

## Overview

The privacy filter protects user information sent to LLMs by anonymizing usernames, detecting and replacing PII (Personally Identifiable Information), and preserving conversation flow. This addresses the concern about leaking user information when sending context to external AI services.

## Features Implemented

### ✅ **Username Anonymization**
- **Consistent Mapping**: `rain` → `User1`, `developer` → `User2` (same across session)
- **Conversation Preservation**: "rain, you don't know" → "User1, you don't know"
- **Common Word Protection**: "I think it will rain tomorrow" (weather) vs "rain, help me" (user addressing)
- **Multiple Patterns**: Direct addressing (`rain,`), mentions (`@rain`), IRC-style (`rain said:`)

### ✅ **PII Detection & Replacement**
- **Email addresses**: `john@example.com` → `[EMAIL]`
- **Phone numbers**: `555-123-4567` → `[PHONE]`
- **IP addresses**: `192.168.1.1` → `[IP_ADDRESS]`
- **SSN**: `123-45-6789` → `[SSN]`
- **Credit cards**: `1234 5678 9012 3456` → `[CREDIT_CARD]`
- **GitHub/GitLab URLs**: `https://github.com/user/repo` → `[URL_WITH_USER]/repo`

### ✅ **Performance Optimization**
- **Channel Size Limits**: Skip privacy for channels with >20 users (configurable)
- **Efficient Processing**: Compiled regex patterns for fast matching
- **Memory Management**: Per-channel user tracking with cleanup options

### ✅ **Conversation Flow Preservation**
- **Addressing Detection**: Recognizes when users are talking TO vs ABOUT someone
- **Context Awareness**: "rain said the weather is nice" vs "rain, what's the weather?"
- **Natural Language**: Maintains conversation meaning while protecting privacy

## Configuration

Add these settings to your `.env` file:

```bash
# Privacy Filter Settings
PRIVACY_FILTER_ENABLED=true                    # Enable/disable privacy filtering
PRIVACY_LEVEL=medium                           # none, low, medium, high, paranoid
PRIVACY_MAX_CHANNEL_USERS=20                   # Skip privacy for large channels (performance)
PRIVACY_USERNAME_ANONYMIZATION=true            # Anonymize usernames
PRIVACY_PII_DETECTION=true                     # Detect and replace PII
PRIVACY_PRESERVE_CONVERSATION_FLOW=true        # Try to maintain addressing context
```

### Privacy Levels

- **`none`**: No privacy filtering (original behavior)
- **`low`**: Basic username anonymization only
- **`medium`**: Username anonymization + common PII detection (recommended)
- **`high`**: Aggressive PII detection + content sanitization
- **`paranoid`**: Remove all context, question-only mode

## Bot Commands

### `!privacy`
Shows privacy statistics for the current channel:
```
🔒 Privacy Stats for #dev:
• Privacy Level: medium
• Active Users: 8
• Mapped Users: 6
• Max Channel Size: 20
• Privacy Status: ✅ Applied
```

### `!privacy test <message>`
Test privacy filtering on a sample message:
```
🔒 Privacy Filter Test for #dev:
• Original: rain, my email is test@example.com
• Sanitized: User1, my email is [EMAIL]
• Your username: developer → User2
• Known users in channel: 5
```

### `!privacy clear`
Clear privacy mappings for the channel (admin feature):
```
🧹 Privacy data cleared for #dev
```

## Example Scenarios

### Scenario 1: Direct Addressing with Common Word Username
```
Original: "rain, you don't know what you're talking about"
Protected: "User1, you don't know what you're talking about"
✅ Preserves conversation meaning while protecting username
```

### Scenario 2: Weather Discussion (NOT user addressing)
```
Original: "I think it's going to rain tomorrow"
Protected: "I think it's going to rain tomorrow"
✅ Correctly identifies this is about weather, not the user 'rain'
```

### Scenario 3: Technical Support with PII
```
Original: "My server at 192.168.1.1 is down, email me at admin@company.com"
Protected: "My server at [IP_ADDRESS] is down, email me at [EMAIL]"
✅ Protects sensitive information
```

### Scenario 4: Large Channel Performance
```
Channel with 25 users (> 20 limit):
Original: "user5, can you help me?"
Protected: "user5, can you help me?" (unchanged)
✅ Privacy skipped for performance, logged for transparency
```

## Technical Implementation

### Context Manager Integration
```python
# Privacy filter is automatically integrated
formatted_context = context_manager.format_context_for_llm(messages)
# Returns privacy-protected context ready for LLM
```

### LLM Handler Integration
The privacy filter is transparent to existing LLM calls:
```python
# Before privacy:
response = llm_handler.ask_llm(question, raw_context)

# After privacy (automatic):
response = llm_handler.ask_llm(question, privacy_protected_context)
```

## Benefits

### **Security**
- ✅ Protects user privacy when using external AI services
- ✅ Prevents accidental PII exposure in logs/monitoring
- ✅ Configurable protection levels for different security needs

### **Performance**
- ✅ Automatic bypass for large channels (configurable threshold)
- ✅ Efficient regex-based processing
- ✅ Minimal memory overhead with per-channel tracking

### **Usability**
- ✅ Preserves conversation meaning and flow
- ✅ Consistent username mappings across sessions
- ✅ Smart detection of addressing vs references
- ✅ Transparent to existing bot functionality

## Limitations & Considerations

### **Common Word Usernames**
The system handles common words like "rain", "dog", "fire" by:
- Only replacing in addressing contexts ("rain," or "@rain")
- Preserving natural language usage ("it will rain tomorrow")
- Using conversation pattern detection

### **Channel Size Performance**
- Default limit: 20 users per channel
- Larger channels skip privacy filtering for performance
- Configurable threshold based on your server capacity
- Logged when privacy is skipped for transparency

### **Mapping Persistence**
- Username mappings persist within session
- Clear mappings with `!privacy clear` command
- Consider implementing database persistence for long-term consistency

## Testing

Run comprehensive tests:
```bash
# Full test suite
python3 test_privacy_filter.py

# Integration testing
python3 test_integration.py

# Interactive demonstration
python3 privacy_demo.py
```

## Migration Guide

1. **Add configuration** to your `.env` file
2. **Deploy updated code** - privacy is opt-in by default
3. **Test in development** with `!privacy test` commands
4. **Monitor performance** in production channels
5. **Adjust settings** as needed for your community

The privacy filter is designed to be:
- **Non-breaking**: Existing functionality unchanged
- **Configurable**: Adapt to your privacy needs
- **Performant**: Minimal impact on bot response times
- **Transparent**: Clear visibility into what's being protected

## Support

For issues or questions:
1. Check the test output for validation
2. Use `!privacy` commands to verify operation
3. Adjust `PRIVACY_LEVEL` and `PRIVACY_MAX_CHANNEL_USERS` as needed
4. Review logs for performance impact and privacy bypass notifications
