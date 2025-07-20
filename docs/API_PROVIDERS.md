# API Providers

aix supports multiple AI providers because variety is the spice of life (and sometimes OpenAI is down).

## Supported Providers

### OpenRouter (Default)
- **Model**: `meta-llama/llama-3.2-3b-instruct:free`
- **Cost**: Free tier available
- **Pros**: Multiple models, great free options
- **Cons**: Rate limits on free tier

### OpenAI
- **Model**: `gpt-3.5-turbo`
- **Cost**: Pay-per-use
- **Pros**: Fast, reliable
- **Cons**: Requires payment method

### Anthropic
- **Model**: `claude-3-haiku-20240307`
- **Cost**: Pay-per-use
- **Pros**: Great at following instructions
- **Cons**: Can be expensive for heavy use

### Custom Providers
- **Model**: User-defined
- **Cost**: Varies by provider
- **Pros**: Use local models (Ollama), custom endpoints, specialized services
- **Cons**: Requires manual setup

See [CUSTOM_PROVIDERS.md](CUSTOM_PROVIDERS.md) for detailed setup instructions.

## Setting Up API Keys

### Interactive Setup
```bash
# Set up OpenRouter (recommended for beginners)
aix api-key openrouter

# Set up OpenAI
aix api-key openai

# Set up Anthropic
aix api-key anthropic

# Set up custom provider
aix api-key custom:provider-name
```

### Manual Setup
```bash
# Direct configuration
aix config --set api_keys.openrouter "your-key-here"
aix config --set api_keys.openai "your-key-here"
aix config --set api_keys.anthropic "your-key-here"
```

## Switching Providers

### Per Command
```bash
# Use specific provider for a single run
aix run my-prompt --provider openai --execute
aix run my-prompt --provider anthropic --execute
```

### Set Default
```bash
# Make OpenAI your default
aix config --set default_provider openai

# Back to OpenRouter
aix config --set default_provider openrouter
```

## Provider-Specific Models

### OpenRouter Models
```bash
# List available models (requires API key)
curl -H "Authorization: Bearer YOUR_KEY" https://openrouter.ai/api/v1/models

# Popular models:
# - meta-llama/llama-3.2-3b-instruct:free (free)
# - anthropic/claude-3.5-sonnet (paid)
# - openai/gpt-4o-mini (paid)
```

### OpenAI Models
```bash
# Use GPT-4
aix run my-prompt --provider openai --model gpt-4 --execute

# Use GPT-3.5
aix run my-prompt --provider openai --model gpt-3.5-turbo --execute
```

### Anthropic Models
```bash
# Use Claude 3.5 Sonnet
aix run my-prompt --provider anthropic --model claude-3-5-sonnet-20241022 --execute

# Use Claude 3 Haiku (default)
aix run my-prompt --provider anthropic --execute
```

## Advanced Configuration

### Custom Models
```bash
# Set custom model for provider
aix config --set openai_default_model "gpt-4"
aix config --set anthropic_default_model "claude-3-5-sonnet-20241022"
```

### Cost Optimization
```bash
# Use free tier by default
aix config --set default_provider openrouter
aix config --set default_model "meta-llama/llama-3.2-3b-instruct:free"
```

## Troubleshooting

### "No API key found"
```bash
# Check current keys
aix config --list | grep api_keys

# Set missing key
aix api-key [provider]
```

### Rate Limits
```bash
# Switch to free tier if hitting limits
aix config --set default_model "meta-llama/llama-3.2-3b-instruct:free"
```

### Provider Down
```bash
# Quick switch to backup provider
aix run my-prompt --provider [other-provider] --execute
```

## API Key Security

- Keys are stored in `~/.prompts/config.json`
- File permissions are set to 600 (user-only read/write)
- Never commit API keys to version control
- Use environment variables for CI/CD:
  ```bash
  export OPENAI_API_KEY="your-key"
  export ANTHROPIC_API_KEY="your-key"
  ```