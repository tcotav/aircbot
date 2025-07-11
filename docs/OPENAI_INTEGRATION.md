# OpenAI API Integration

This document describes the OpenAI API integration added to AircBot, which provides flexible AI service options.

## 🎯 Overview

AircBot now supports three different LLM modes:
1. **local_only** - Use only local AI (Ollama) - Default mode
2. **openai_only** - Use only OpenAI API  
3. **fallback** - Try local AI first, fall back to OpenAI if needed

## ⚙️ Configuration

### Environment Variables

```bash
# LLM Mode Selection
LLM_MODE=fallback  # local_only | openai_only | fallback

# Local LLM (Ollama) Settings
LLM_ENABLED=true
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=deepseek-r1:latest
LLM_MAX_TOKENS=150
LLM_TEMPERATURE=0.7
LLM_RETRY_ATTEMPTS=3

# OpenAI Settings
OPENAI_ENABLED=true
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=150
OPENAI_TEMPERATURE=0.7
```

### Mode Examples

**Local Only** (free, private, no internet required for queries):
```bash
LLM_MODE=local_only
LLM_ENABLED=true
OPENAI_ENABLED=false
```

**OpenAI Only** (always use OpenAI API):
```bash
LLM_MODE=openai_only
LLM_ENABLED=false
OPENAI_ENABLED=true
OPENAI_API_KEY=sk-your-key-here
```

**Smart Fallback** (best of both worlds):
```bash
LLM_MODE=fallback
LLM_ENABLED=true
OPENAI_ENABLED=true
OPENAI_API_KEY=sk-your-key-here
```

## 🔄 Fallback Logic

In fallback mode, the bot:
1. **First** tries the local AI (Ollama)
2. **If local fails** or gives a poor response, automatically uses OpenAI
3. **Poor responses** include:
   - "I don't know" responses
   - Very short responses (< 10 characters)
   - Error responses
   - Empty responses

## 📊 Performance Monitoring

The `!performance` command now shows separate stats for each service:

```
📊 LLM Performance Stats (Mode: fallback):
• Local: 12 requests, 91.7% success, avg: 0.8s (range: 0.5s-1.2s)
• OpenAI: 3 requests, 100% success, avg: 1.5s (range: 1.2s-1.8s)  
• Overall: 15 total, 2 failed
```

## 🧪 Testing

Run the integration test to verify all modes work:

```bash
python test_openai_integration.py
```

This tests all three modes and shows which clients are enabled.

## 💡 Benefits

### Local Only Mode
- **Free** - No API costs
- **Private** - Data never leaves your server
- **Fast** - No network latency for queries
- **Reliable** - Works without internet

### OpenAI Only Mode  
- **High Quality** - Consistently good responses
- **Reliable** - 99%+ uptime
- **Latest Models** - Access to GPT-4, etc.

### Fallback Mode
- **Best of Both** - Speed + reliability of local with quality backup
- **Cost Effective** - Only uses paid API when needed
- **Automatic** - No manual intervention required
- **Transparent** - Detailed logging shows which service handled each request

## 🔧 Implementation Details

- **Dual Client Support** - Maintains separate OpenAI clients for local and remote
- **Smart Routing** - Automatic request routing based on mode
- **Separate Stats** - Independent performance tracking for each service
- **Graceful Fallback** - Seamless transition between services
- **Backward Compatible** - Existing configurations continue to work

## 📝 Migration Guide

Existing bots continue working unchanged. To enable OpenAI integration:

1. Add OpenAI configuration to `.env`
2. Set `LLM_MODE=fallback` for smart fallback
3. Or set `LLM_MODE=openai_only` for OpenAI only
4. Monitor with `!performance` command

The integration is fully backward compatible - no changes required for existing deployments.
