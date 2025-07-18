# aix

AI executor - dynamic prompt management and execution tool that brings the power of AI to your command line. Create, organize, and execute dynamic prompts with built-in API integration and command execution capabilities.

## Features

### Prompt Management
- Create reusable prompt templates with `{variable}` syntax
- Save prompts in JSON or YAML format
- Organize prompts with tags and descriptions
- Store prompts in `~/.prompts` directory

### AI Integration
- Execute prompts via multiple AI providers:
  - **OpenRouter** - Access to 100+ models through one API
  - **OpenAI** - GPT models (GPT-4, GPT-3.5-turbo, etc.)
  - **Anthropic** - Claude models (Opus, Sonnet, Haiku)
- Streaming and non-streaming responses
- Token usage tracking and cost estimation
- Configurable models and parameters

### Dynamic Command Execution
- Embed shell commands directly in prompts
- Multiple syntax options: `$(git status)`, `{cmd:ls}`, `{exec:pwd}`
- Security-first approach with allowlisted commands
- Real-time system information integration

### Organization & Management
- List all saved prompts with details
- Search and filter capabilities
- Delete unwanted prompts
- Export/import prompt collections

### Configuration
- Secure API key management
- Configurable storage location
- Default providers and models
- Customizable settings

## Quick Start

### Installation

```bash
# Install with uv (recommended)
uv tool install aix --from git+https://github.com/bhadzhiev/prompt.git

# Or install with pip
pip install git+https://github.com/bhadzhiev/prompt.git
```

### Basic Usage

```bash
# Create your first prompt
aix create "code-review" "Please review this {language} code: {code}" --desc "Code review template"

# List all prompts
aix list

# Run a prompt with variables
aix run code-review --param language=Python --param code="print('hello')"

# Execute via AI (requires API key)
aix run code-review --param language=Python --param code="print('hello')" --execute
```

## Documentation

### Setting Up API Keys

Choose your preferred AI provider and set up the API key:

```bash
# OpenRouter (recommended - access to 100+ models)
aix api-key openrouter

# OpenAI
aix api-key openai

# Anthropic
aix api-key anthropic
```

**New to AI?** Check out our [OpenRouter Guide](OPENROUTER.md) for free models and setup instructions!

### Creating Dynamic Prompts

Create prompts that automatically include system information:

```bash
aix create "system-analysis" "Analyze this development environment:
- Current user: $(whoami)
- Working directory: $(pwd)
- Git status: $(git status --porcelain)
- Recent commits: {cmd:git log --oneline -5}
- Python version: {exec:python --version}

Suggestions for {project_type} development?"
```

### Running Dynamic Prompts

```bash
# Enable command execution
aix run system-analysis --param project_type="web app" --enable-commands --dry-run

# With specific provider and model
aix run system-analysis --param project_type="API" --enable-commands --execute --provider openai --model gpt-4
```

## Command Reference

### Core Commands

| Command | Description | Example |
|---------|-------------|---------|
| `create` | Create a new prompt template | `aix create "name" "template"` |
| `list` | List all saved prompts | `aix list` |
| `show` | Show detailed prompt information | `aix show prompt-name` |
| `delete` | Delete a prompt | `aix delete prompt-name` |
| `run` | Execute a prompt | `aix run prompt-name --execute` |

### Configuration Commands

| Command | Description | Example |
|---------|-------------|---------|
| `config` | Manage settings | `aix config --list` |
| `api-key` | Manage API keys | `aix api-key openrouter` |

### Command Utilities

| Command | Description | Example |
|---------|-------------|---------|
| `cmd test` | Test command execution | `aix cmd test "git status"` |
| `cmd list` | Show allowed commands | `aix cmd list` |
| `cmd template-test` | Test template with commands | `aix cmd template-test "Hello $(whoami)"` |

### Run Command Options

| Option | Description | Example |
|--------|-------------|---------|
| `--param` | Set template variables | `--param key=value` |
| `--execute` | Execute via AI API | `--execute` |
| `--provider` | Choose AI provider | `--provider openai` |
| `--model` | Specify model | `--model gpt-4` |
| `--stream` | Stream response | `--stream` |
| `--enable-commands` | Enable command execution | `--enable-commands` |
| `--dry-run` | Preview without execution | `--dry-run` |
| `--output` | Save to file | `--output result.txt` |

## Security

### Command Execution Security
- **Allowlisted Commands**: Only predefined safe commands are allowed
- **Timeout Protection**: Commands automatically timeout after 30 seconds
- **Shell Injection Protection**: Safe command parsing and execution
- **User Control**: Command execution is opt-in via `--enable-commands`

### API Key Security
- Keys are stored securely in local configuration
- Masked display in configuration listings
- Per-provider key management

## File Structure

```
~/.prompts/
├── config.json          # Configuration and API keys
├── my-prompt.yaml       # Individual prompt files
├── code-review.json     # Prompts can be JSON or YAML
└── ...
```

## Supported Models

### OpenRouter (100+ models available)
- `meta-llama/llama-3.2-3b-instruct:free` (default, free)
- `meta-llama/llama-3.1-70b-instruct`
- `anthropic/claude-3-sonnet`
- `openai/gpt-4`
- `mistralai/mistral-7b-instruct:free`

### OpenAI
- `gpt-4` / `gpt-4-turbo`
- `gpt-3.5-turbo` (default)

### Anthropic
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307` (default)

## Examples

### Code Review
```bash
# Create
aix create "review" "Review this {lang} code:\n\n{code}\n\nFocus: bugs, style, performance"

# Use (dry run to preview)
aix run review --param lang=Python --param code="def fact(n): return 1 if n<=1 else n*fact(n-1)" --dry-run

# Execute with AI (requires API key)
aix run review --param lang=Python --param code="def fact(n): return 1 if n<=1 else n*fact(n-1)" --execute
```

### Git Helper
```bash
# Create
aix create "commit" "Write commit message:\n\nChanges:\n$(git diff --staged)\n\nFollow conventional commits."

# Use (dry run to preview)
aix run commit --enable-commands --dry-run

# Execute with AI (requires API key)
aix run commit --enable-commands --execute
```

### Documentation
```bash
# Create
aix create "docs" "Document {lang} {type}:\n\nFile: {file}\nCode: {code}\n\nInclude: description, params, examples"

# Use (dry run to preview)
aix run docs --param lang=Python --param type=function --param file=utils.py --param code="def load_data(path): ..." --dry-run

# Execute with AI (requires API key)
aix run docs --param lang=Python --param type=function --param file=utils.py --param code="def load_data(path): ..." --execute
```

## Configuration

### Default Settings
```bash
# View current configuration
aix config --list

# Set default provider
aix config default_provider openrouter

# Set default models
aix config default_model "meta-llama/llama-3.1-70b-instruct"
aix config openai_default_model "gpt-4"

# Configure generation parameters
aix config temperature 0.8
aix config max_tokens 2048
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT

## Support

If you encounter any issues or have questions:
1. Check the documentation above
2. Test commands with `promptconsole cmd test "your-command"`
3. View configuration with `promptconsole config --list`
4. Create an issue on GitHub

---

**Made for developers who love automation and AI**