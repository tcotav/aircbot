# Claude Development Commands & Workflows

This file documents common commands and workflows used for developing the AircBot project with Claude Code.

## Virtual Environment Setup

```bash
# Activate the virtual environment (from project root)
source venv/bin/activate
```

## Testing Commands

```bash
# Run tests with virtual environment
source venv/bin/activate && python test_filename.py

# Run Python scripts
python3 script_name.py

# Run with activated venv
source venv/bin/activate && python script_name.py

# Run fallback logic tests
source venv/bin/activate && python tests/test_fallback_logic.py

# Run tests with custom fallback configuration
FALLBACK_MIN_RESPONSE_LENGTH=5 source venv/bin/activate && python tests/test_fallback_logic.py
```

## File Management

```bash
# Remove test files
rm test_filename.py

# Check if files exist
ls -la filename.txt

# Create example files
echo "content here" > filename.txt.example
```

## Development Workflow - Adding New Features

### 1. Analysis Phase
- Use `Read` tool to examine existing code structure
- Use `Glob` to find relevant files by pattern
- Use `Grep` to search for specific code patterns
- Use `Task` tool for complex searches across codebase

### 2. Implementation Phase
- Use `TodoWrite` to track implementation tasks
- Use `Edit` tool to modify existing files
- Use `Write` tool to create new files
- Use `MultiEdit` for multiple changes to same file

### 3. Testing Phase
- Create test scripts to verify functionality
- Run tests with virtual environment
- Clean up test files after verification

## Code Search Patterns

```bash
# Find files with specific patterns
*.py              # All Python files
*config*          # Files with 'config' in name
*.json            # JSON configuration files
*.yml, *.yaml     # YAML files

# Search for code patterns
llm_handler|LLMHandler    # Find LLM handler usage
get_system_prompt         # Find system prompt usage
```

## Project Structure Understanding

### Key Files for Bot Development
- `bot.py` - Main bot logic and IRC handling
- `config.py` - Configuration management
- `llm_handler.py` - LLM integration and API calls
- `prompts.py` - Prompt templates and system messages
- `database.py` - Database operations
- `content_filter.py` - Content filtering
- `context_manager.py` - Message context handling

### Configuration Pattern
1. Add new config variables to `config.py`
2. Add validation logic if needed
3. Update relevant handlers to use new config
4. Test with example configurations

## Feature Development Example - Personality Prompts

### Files Modified:
- `config.py` - Added personality configuration and validation
- `prompts.py` - Updated system prompt generation
- `llm_handler.py` - Updated to pass config to prompt functions

### Configuration Added:
```python
# In config.py
PERSONALITY_ENABLED = os.getenv('PERSONALITY_ENABLED', 'false').lower() == 'true'
PERSONALITY_PROMPT_FILE = os.getenv('PERSONALITY_PROMPT_FILE', 'personality_prompt.txt')
```

### Usage:
```bash
# Enable personality
export PERSONALITY_ENABLED=true
export PERSONALITY_PROMPT_FILE=personality_prompt.txt

# Create personality file
echo "Your personality prompt here" > personality_prompt.txt
```

## Common Git Commands

```bash
# Check status
git status

# Add files
git add filename.py

# Commit changes
git commit -m "Add personality prompt feature

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

# Check recent commits
git log --oneline -n 5
```

## Debugging & Troubleshooting

### Module Import Issues
- Always activate virtual environment first
- Check if required packages are installed
- Verify Python path includes project directory

### Configuration Issues
- Check environment variables are set
- Verify file paths are correct
- Look for validation errors in config.py

### Testing Issues
- Run tests from project root directory
- Ensure virtual environment is activated
- Clean up test files after use

## Best Practices

1. **Always use TodoWrite** to track complex tasks
2. **Test incrementally** - create small test scripts for new features
3. **Follow existing patterns** - examine similar functionality first
4. **Clean up** - remove test files and temporary code
5. **Document** - update this file with new workflows
6. **Error handling** - add proper validation for new config options
7. **Fallback configuration** - use test suite to validate settings before deployment
8. **Monitor fallback rates** - aim for 10-20% fallback rate in normal operation

## LLM Fallback Configuration

The bot includes enhanced fallback logic that determines when to switch from local LLM to OpenAI based on response quality. This is only active when `LLM_MODE=fallback`.

### Key Configuration Settings

```bash
# Basic response filtering
export FALLBACK_MIN_RESPONSE_LENGTH=3              # Min chars for valid response
export FALLBACK_DONT_KNOW_CONTEXT_MIN_WORDS=15     # Context check for uncertain responses

# Relevance scoring
export FALLBACK_RELEVANCE_MIN_RATIO=0.05           # Min keyword overlap ratio
export FALLBACK_RELEVANCE_MIN_QUESTION_WORDS=3     # Min question words for relevance check

# Response quality thresholds
export FALLBACK_GENERIC_RESPONSE_MAX_WORDS=25      # Max words for generic responses
export FALLBACK_EXPLANATION_MIN_WORDS=8            # Min words for explanations
export FALLBACK_REPETITION_MAX_WORD_RATIO=0.3      # Max word repetition ratio
```

### Semantic Similarity Configuration

The bot now supports semantic similarity scoring for more intelligent fallback decisions. This feature uses sentence-transformers to evaluate response relevance beyond simple keyword matching.

```bash
# Enable semantic similarity scoring (requires sentence-transformers)
export SEMANTIC_SIMILARITY_ENABLED=true            # Enable semantic similarity scoring
export SEMANTIC_SIMILARITY_MIN_THRESHOLD=0.3       # Min similarity score to pass (0.0-1.0)
export SEMANTIC_SIMILARITY_WEIGHT=0.4              # Weight in combined scoring (0.0-1.0)

# Model configuration
export SEMANTIC_MODEL_NAME=all-MiniLM-L6-v2        # Sentence transformer model
export SEMANTIC_MODEL_DEVICE=cpu                   # 'cpu' or 'cuda'
export SEMANTIC_CACHE_SIZE=100                     # Cache size for embeddings

# Context-aware scoring
export SEMANTIC_CONTEXT_ENABLED=true               # Enable context-aware scoring
export SEMANTIC_CONTEXT_WEIGHT=0.2                 # Weight for context matching (0.0-1.0)

# Technical keyword boosting
export SEMANTIC_ENTITY_BOOST=1.2                   # Boost factor for technical terms
export SEMANTIC_TECHNICAL_KEYWORDS="code,function,class,api,database,server,config,install,debug,error,fix,implement,create,build,deploy,test,python,javascript,sql,git,docker,linux,windows,network,security,performance"
```

### Common Configurations

**Permissive (IRC/Casual):**
```bash
export FALLBACK_MIN_RESPONSE_LENGTH=2
export FALLBACK_RELEVANCE_MIN_RATIO=0.03
export FALLBACK_EXPLANATION_MIN_WORDS=5
export SEMANTIC_SIMILARITY_ENABLED=false  # Disable for casual use
```

**Strict (Technical/Educational):**
```bash
export FALLBACK_MIN_RESPONSE_LENGTH=5
export FALLBACK_RELEVANCE_MIN_RATIO=0.15
export FALLBACK_EXPLANATION_MIN_WORDS=15
export SEMANTIC_SIMILARITY_ENABLED=true   # Enable for technical discussions
export SEMANTIC_SIMILARITY_MIN_THRESHOLD=0.4
export SEMANTIC_ENTITY_BOOST=1.3
```

**Performance-Optimized (Resource-Conscious):**
```bash
export SEMANTIC_SIMILARITY_ENABLED=false  # Disable to save resources
export SEMANTIC_CACHE_SIZE=50              # Smaller cache if enabled
export SEMANTIC_MODEL_DEVICE=cpu           # Use CPU instead of GPU
```

### Testing Fallback Configuration

```bash
# Run fallback tests with default settings
source venv/bin/activate && python tests/test_fallback_logic.py

# Test with custom configuration
FALLBACK_MIN_RESPONSE_LENGTH=5 FALLBACK_RELEVANCE_MIN_RATIO=0.1 source venv/bin/activate && python tests/test_fallback_logic.py

# Test semantic similarity functionality
source venv/bin/activate && python tests/test_semantic_similarity.py

# Test with semantic similarity enabled
SEMANTIC_SIMILARITY_ENABLED=true source venv/bin/activate && python tests/test_semantic_similarity.py
```

See `docs/FALLBACK_CONFIGURATION.md` for detailed explanation of all settings.

## Environment Variables Reference

```bash
# Core bot settings
export IRC_SERVER=irc.libera.chat
export IRC_NICKNAME=aircbot
export IRC_CHANNEL=#yourchannel

# LLM settings
export LLM_ENABLED=true
export LLM_MODE=local_only  # or openai_only, fallback

# Personality settings
export PERSONALITY_ENABLED=true
export PERSONALITY_PROMPT_FILE=personality_prompt.txt

# Rate limiting
export RATE_LIMIT_USER_PER_MINUTE=1
export RATE_LIMIT_TOTAL_PER_MINUTE=10
```

## File Templates

### Test Script Template
```python
#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from module_to_test import function_to_test

def test_feature():
    """Test description"""
    # Test implementation
    assert condition
    print("✓ Test passed")

if __name__ == "__main__":
    test_feature()
    print("✅ All tests passed!")
```

### Configuration Addition Template
```python
# In config.py
FEATURE_ENABLED = os.getenv('FEATURE_ENABLED', 'false').lower() == 'true'
FEATURE_SETTING = os.getenv('FEATURE_SETTING', 'default_value')

# Add validation if needed
if FEATURE_ENABLED:
    # Validation logic here
    pass
```