# Custom API Providers

AIX supports adding custom API providers for any OpenAI-compatible endpoint. This allows you to use local models, self-hosted APIs, or any other service that follows the OpenAI API specification.

## Quick Start

```bash
# Add a custom provider (e.g., local Ollama)
aix provider add "ollama" "http://localhost:11434/v1" \
  --model "llama3.2" \
  --header "X-Custom-Header:value"

# List all custom providers
aix provider list

# Use custom provider
aix run my-prompt --provider custom:ollama

# Get provider details
aix provider info ollama

# Remove provider
aix provider remove ollama
```

## Adding Custom Providers

### Basic Provider

```bash
aix provider add "local-api" "http://localhost:8080/v1"
```

### Provider with Default Model

```bash
aix provider add "ollama" "http://localhost:11434/v1" --model "llama3.2"
```

### Provider with Custom Headers

```bash
aix provider add "custom-service" "https://api.example.com/v1" \
  --header "X-API-Key:your-api-key" \
  --header "X-Service-Version:v2"
```

### Provider with Different Auth Type

```bash
aix provider add "api-key-service" "https://api.example.com/v1" \
  --auth-type "api-key" \
  --header "Authorization:Bearer custom-token"
```

## Using Custom Providers

### Running Prompts

```bash
# Use custom provider
aix run my-prompt --provider custom:ollama

# Override default model
aix run my-prompt --provider custom:ollama --model "different-model"

# With streaming
aix run my-prompt --provider custom:ollama --stream
```

### Setting API Keys

Custom providers use the same API key system as built-in providers:

```bash
# Set API key for custom provider
aix api-key ollama

# Or set in config manually
aix config set api_keys.ollama "your-api-key"
```

## Provider Configuration

Each custom provider supports the following configuration:

| Option | Description | Required | Default |
|--------|-------------|----------|---------|
| `name` | Unique identifier for the provider | ✅ | - |
| `base_url` | API endpoint URL | ✅ | - |
| `default_model` | Default model to use | ❌ | None |
| `headers` | Custom HTTP headers | ❌ | `{}` |
| `auth_type` | Authentication type | ❌ | `bearer` |

### Headers Format

Headers are specified as `key:value` pairs:

```bash
aix provider add "example" "http://api.example.com/v1" \
  --header "Content-Type:application/json" \
  --header "X-Custom-Auth:bearer-token" \
  --header "X-API-Version:2.0"
```

### Authentication Types

- `bearer`: Uses `Authorization: Bearer {api_key}` header
- `api-key`: Uses custom authentication (configure with headers)

## Common Use Cases

### Local Ollama

```bash
# Add Ollama provider
aix provider add "ollama" "http://localhost:11434/v1" \
  --model "llama3.2"

# Use Ollama (no API key needed for local)
aix run my-prompt --provider custom:ollama
```

### OpenAI-Compatible Services

```bash
# Add compatible service
aix provider add "openai-compat" "https://api.example.com/v1" \
  --model "gpt-3.5-turbo-equivalent"

# Set API key
aix api-key openai-compat

# Use service
aix run my-prompt --provider custom:openai-compat
```

### Self-Hosted Models

```bash
# Add self-hosted API
aix provider add "self-hosted" "https://my-api.company.com/v1" \
  --model "company-model-v2" \
  --header "X-Company-Auth:internal-key"

# Use with company API key
aix api-key self-hosted
aix run my-prompt --provider custom:self-hosted
```

### vLLM or FastAPI Deployments

```bash
# Add vLLM deployment
aix provider add "vllm" "http://localhost:8000/v1" \
  --model "meta-llama/Llama-2-7b-chat-hf"

# Use vLLM deployment
aix run my-prompt --provider custom:vllm
```

## Provider Management

### List All Providers

```bash
aix provider list
```

Shows a table with all configured custom providers including their base URLs, default models, and authentication types.

### Get Provider Information

```bash
aix provider info <name>
```

Shows detailed configuration for a specific provider including custom headers.

### Update Provider

To update a provider, remove it and add it again:

```bash
aix provider remove old-config
aix provider add updated-config "http://new-url.com/v1" --model "new-model"
```

### Remove Provider

```bash
aix provider remove <name>
```

## API Compatibility Requirements

Custom providers must implement OpenAI-compatible endpoints:

### Required Endpoint

- `POST /chat/completions` - For text generation

### Request Format

```json
{
  "model": "model-name",
  "messages": [{"role": "user", "content": "prompt"}],
  "stream": false
}
```

### Response Format

```json
{
  "choices": [
    {
      "message": {
        "content": "generated response"
      }
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20
  }
}
```

### Streaming Support

For streaming responses, the provider should support:
- `stream: true` in request
- Server-sent events in response
- `data: ` prefixed JSON chunks
- `data: [DONE]` to end stream

## Troubleshooting

### Provider Not Found

```
Custom provider 'name' not found
```

**Solution**: Check provider name with `aix provider list` and ensure you use `custom:name` format.

### Connection Errors

```
Connection failed to http://localhost:11434/v1
```

**Solutions**:
- Verify the service is running
- Check the base URL is correct
- Ensure network connectivity

### Authentication Errors

```
401 Unauthorized
```

**Solutions**:
- Set API key: `aix api-key provider-name`
- Check custom headers are correct
- Verify auth_type matches service expectations

### Model Not Available

```
Model 'model-name' not found
```

**Solutions**:
- Check available models on your service
- Update default model: `aix provider remove name && aix provider add name url --model correct-model`
- Override model in run command: `--model available-model`

## Examples

### Complete Ollama Setup

```bash
# Install and start Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve

# Pull a model
ollama pull llama3.2

# Add to AIX
aix provider add "ollama" "http://localhost:11434/v1" --model "llama3.2"

# Create a prompt
aix create "explain" "Explain this concept: {concept}"

# Use Ollama
aix run explain --param concept="machine learning" --provider custom:ollama --execute
```

### Complete vLLM Setup

```bash
# Start vLLM server (example)
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-2-7b-chat-hf \
  --port 8000

# Add to AIX
aix provider add "vllm" "http://localhost:8000/v1" \
  --model "meta-llama/Llama-2-7b-chat-hf"

# Use vLLM
aix run my-prompt --provider custom:vllm --execute
```

## Advanced Configuration

### Environment-Specific Providers

```bash
# Development
aix provider add "dev-api" "http://localhost:8080/v1" --model "dev-model"

# Staging  
aix provider add "staging-api" "https://staging-api.company.com/v1" --model "staging-model"

# Production
aix provider add "prod-api" "https://api.company.com/v1" --model "prod-model"
```

### Provider with Complex Headers

```bash
aix provider add "complex-api" "https://api.example.com/v1" \
  --header "Authorization:Bearer static-token" \
  --header "X-API-Version:2024-01" \
  --header "X-Client-ID:aix-client" \
  --header "Accept:application/json"
```

## Configuration Storage

Custom provider configurations are stored in `~/.prompts/config.json`:

```json
{
  "custom_providers": {
    "ollama": {
      "base_url": "http://localhost:11434/v1",
      "default_model": "llama3.2",
      "headers": {"X-Custom": "value"},
      "auth_type": "bearer"
    }
  }
}
```

This allows for manual editing if needed, though the CLI commands are recommended.