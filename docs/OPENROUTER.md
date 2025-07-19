# OpenRouter Guide - Free AI Models with aix

## What is OpenRouter?

**OpenRouter** is a unified API that gives you access to 100+ AI models from different providers through a single interface. Think of it as the "Netflix of AI models" - one API key unlocks access to models from OpenAI, Anthropic, Google, Meta, and many more.

### Key Benefits
- Free tier available - 20+ models completely free
- One API key - Access 100+ models
- Pay-as-you-go - No monthly subscriptions for paid models
- Model switching - Change models without code changes
- Usage tracking - Monitor costs per model

## Quick Setup

```bash
# Set up OpenRouter API key
aix api-key openrouter

# Verify it works
aix config --list
```

## Best Free Models

### Meta Llama 3.2 3B - `meta-llama/llama-3.2-3b-instruct:free`
- **Use cases**: General chat, simple coding, brainstorming
- **Strengths**: Fast responses, good for basic tasks
- **Limitations**: Smaller context window, less complex reasoning

### Mistral 7B - `mistralai/mistral-7b-instruct:free`
- **Use cases**: Code review, technical documentation, translations
- **Strengths**: Strong coding abilities, good instruction following
- **Limitations**: Can be verbose, occasional hallucinations

### Gemma 2 9B - `google/gemma-2-9b-it:free`
- **Use cases**: Creative writing, content generation, summarization
- **Strengths**: Natural language, creative tasks
- **Limitations**: Less technical knowledge

## Model Recommendations by Task

### Code Review & Debugging
```bash
# Free option
aix config default_model "meta-llama/llama-3.2-3b-instruct:free"

# Premium option (paid)
aix config default_model "anthropic/claude-3-sonnet"
```

### Documentation Writing
```bash
# Free option
aix config default_model "mistralai/mistral-7b-instruct:free"

# Premium option (paid)
aix config default_model "openai/gpt-4"
```

### Creative Writing
```bash
# Free option
aix config default_model "google/gemma-2-9b-it:free"

# Premium option (paid)
aix config default_model "anthropic/claude-3-opus"
```

### Complex Reasoning
```bash
# Free option (limited)
aix config default_model "meta-llama/llama-3.2-3b-instruct:free"

# Premium option (paid)
aix config default_model "openai/gpt-4-turbo"
```

## Configuration Commands

```bash
# Set OpenRouter as default provider
aix config default_provider openrouter

# Set free model as default
aix config default_model "meta-llama/llama-3.2-3b-instruct:free"

# Check your current configuration
aix config --list
```

## Usage Examples

### Quick Test with Free Model
```bash
# Create a simple prompt
aix create "hello" "Hello, I'm {name}! Nice to meet you."

# Test with free model
aix run hello --param name="Developer" --provider openrouter --model meta-llama/llama-3.2-3b-instruct:free --dry-run
```

### Compare Models
```bash
# Test same prompt with different models
aix run hello --param name="Developer" --model meta-llama/llama-3.2-3b-instruct:free --dry-run
aix run hello --param name="Developer" --model mistralai/mistral-7b-instruct:free --dry-run
```

### Code Review with Free Model
```bash
aix create "review-python" "Review this Python code for bugs and improvements:\n\n{code}\n\nProvide specific suggestions."

aix run review-python --param code="def add(a, b): return a + b" --execute
```

## Cost Management

### Free Tier Limits
- **20+ models** completely free
- **Rate limits** apply (usually 10-20 requests/minute)
- **No daily limits** on most free models

### Usage Tracking
```bash
# Check your OpenRouter usage
aix config --list
# Shows API key status and current model
```

### Cost Estimation
- **Free models**: $0.00
- **Paid models**: Range from $0.0001 to $0.03 per 1K tokens
- **Usage dashboard**: https://openrouter.ai/keys

## Switching Between Models

```bash
# Switch to free model
aix config default_model "meta-llama/llama-3.2-3b-instruct:free"

# Switch to premium model
aix config default_model "anthropic/claude-3-sonnet"

# Use specific model for one command
aix run prompt-name --model "openai/gpt-4" --execute
```

## Popular Free Models Reference

| Model | Use Case | Command |
|-------|----------|---------|
| `meta-llama/llama-3.2-3b-instruct:free` | General purpose | `aix config default_model "meta-llama/llama-3.2-3b-instruct:free"` |
| `mistralai/mistral-7b-instruct:free` | Code tasks | `aix config default_model "mistralai/mistral-7b-instruct:free"` |
| `google/gemma-2-9b-it:free` | Creative writing | `aix config default_model "google/gemma-2-9b-it:free"` |
| `microsoft/phi-3-mini-128k-instruct:free` | Quick responses | `aix config default_model "microsoft/phi-3-mini-128k-instruct:free"` |

## Getting Started Checklist

1. **Get API key**: Sign up at https://openrouter.ai/keys
2. **Configure**: `aix api-key openrouter`
3. **Test**: `aix config --list`
4. **Try free model**: `aix run hello --param name="World" --execute`
5. **Experiment**: Try different free models with your prompts

## Troubleshooting

### **"API key invalid"**
- Verify your key at https://openrouter.ai/keys
- Run `aix api-key openrouter` again

### **"Model not found"**
- Check available models: https://openrouter.ai/models
- Ensure you're using the exact model name

### **Rate limits**
- Free models have rate limits
- Try again after a few seconds
- Consider upgrading for higher limits

---

Pro tip: Start with `meta-llama/llama-3.2-3b-instruct:free` for general tasks, then experiment with other free models based on your specific needs!