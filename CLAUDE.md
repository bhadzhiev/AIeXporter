# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PromptConsole** is a comprehensive prompt management and execution tool that brings AI capabilities to the command line. It allows users to create, organize, and execute dynamic prompts with built-in API integration and command execution capabilities.

## Architecture

The codebase follows a modular architecture with these key components:

- **CLI Layer**: `promptconsole/cli.py` - Main Typer-based CLI interface
- **Command Execution**: `promptconsole/command_executor.py` - Safe shell command execution
- **Template System**: `promptconsole/template.py` - Dynamic prompt templating with variables
- **Storage**: `promptconsole/storage.py` - Prompt storage in YAML/JSON formats
- **API Clients**: `promptconsole/api_client.py` - Multi-provider AI API integration
- **Configuration**: `promptconsole/config.py` - User settings and API key management
- **API Keys**: `promptconsole/api_keys.py` - Interactive API key setup
- **Commands**: `promptconsole/commands.py` - CLI command utilities

## Development Setup

### Installation
```bash
# With uv (recommended)
uv sync

# With pip
pip install -e .
```

### Running the Tool
```bash
# Development mode
python main.py --help

# Via installed CLI
promptconsole --help
# or
pc --help
```

### Core Commands

**Create prompts:**
```bash
python main.py create "prompt-name" "Template with {variable}"
```

**List prompts:**
```bash
python main.py list
```

**Run prompts:**
```bash
python main.py run prompt-name --param variable=value --execute
```

**Configuration:**
```bash
python main.py config --list
python main.py api-key openrouter
```

## Key Patterns

### Template Variables
- `{variable}` - Simple variable substitution
- `$(command)` - Shell command execution
- `{cmd:command}` - Alternative command syntax
- `{exec:command}` - Explicit command execution

### Security Model
- Command execution is opt-in via `--enable-commands`
- Allowlisted commands only (configurable in `CommandExecutor`)
- 30-second timeout for command execution
- API keys stored in `~/.prompts/config.json`

### Storage
- Prompts stored in `~/.prompts/` directory
- YAML format by default, JSON supported
- Each prompt as separate file: `{name}.yaml` or `{name}.json`

## API Providers

Supported providers with default models:
- **OpenRouter**: `meta-llama/llama-3.2-3b-instruct:free` (free tier)
- **OpenAI**: `gpt-3.5-turbo`
- **Anthropic**: `claude-3-haiku-20240307`

## Testing

Test command execution:
```bash
python main.py cmd test "git status"
python main.py cmd list
python main.py cmd template-test "Hello $(whoami)"
```

## Configuration Files

- `~/.prompts/config.json` - Main configuration
- `~/.prompts/*.yaml` - Individual prompt files
- `pyproject.toml` - Project dependencies and metadata