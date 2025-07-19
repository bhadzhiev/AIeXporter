# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**aix** (AI eXecutor) is a comprehensive prompt management and execution tool that brings AI capabilities to the command line. It allows users to create, organize, and execute dynamic prompts with built-in API integration and command execution capabilities.

## Development Commands

### Installation and Setup
```bash
# Development installation with uv (recommended)
uv sync

# Alternative with pip
pip install -e .

# Install dev dependencies
pip install -e ".[dev]"
```

### Testing and Quality
```bash
# Run tests with coverage
pytest

# Run tests with coverage report
pytest --cov=promptconsole --cov-report=term-missing

# Type checking
mypy promptconsole/

# Code formatting
black promptconsole/
isort promptconsole/

# Linting
flake8 promptconsole/

# Pre-commit hooks (if configured)
pre-commit run --all-files
```

### Running the Tool
```bash
# Development mode via main.py
python main.py --help

# Via installed CLI (package name: aix)
aix --help

# Direct module execution
python -m promptconsole.cli --help
```

## Architecture

The codebase follows a modular, layered architecture:

### Core Components
- **CLI Layer**: `cli.py` - Main Typer-based CLI with rich console output
- **Template Engine**: `template.py` - Variable substitution and command execution
- **Storage Layer**: `storage.py` - File-based prompt persistence (YAML/JSON)
- **API Layer**: `api_client.py` - Multi-provider AI client abstraction
- **Configuration**: `config.py` - Settings and API key management
- **Command Execution**: `command_executor.py` - Safe shell command execution with allowlisting

### Key Design Patterns
- **Provider Pattern**: `api_client.py` uses factory pattern for different AI providers
- **Template Processing**: Two-stage rendering (variables first, then commands)
- **Storage Separation**: Metadata (`.yaml`/`.json`) and template content (`.txt`) stored separately
- **Command Safety**: Allowlisted commands with configurable timeouts
- **Rich UI**: Extensive use of Rich library for formatted output

### Data Flow
1. User input → CLI parsing (Typer)
2. Prompt loading → Storage layer
3. Template rendering → Variable substitution + command execution
4. API execution → Provider-specific clients
5. Output formatting → Rich console display

## Development Patterns

### Template Variable System
- `{variable}` - Standard variable substitution
- `$(command)` - Shell command execution (requires `--enable-commands`)
- `{cmd:command}` - Alternative command syntax
- `{exec:command}` - Explicit command execution syntax

### Security Model
- Command execution disabled by default
- Allowlisted commands only (see `command_executor.py`)
- 30-second timeout for all command execution
- API keys stored securely in `~/.prompts/config.json`
- No command injection via template variables

### Storage Architecture
- Prompts directory: `~/.prompts/`
- Metadata files: `{name}.yaml` or `{name}.json`
- Template content: `{name}.txt` (separate from metadata)
- Configuration: `config.json` in prompts directory

### API Provider Support
Built-in support for multiple AI providers with unified interface:
- **OpenRouter**: `meta-llama/llama-3.2-3b-instruct:free` (default, free tier)
- **OpenAI**: `gpt-3.5-turbo` (default model)
- **Anthropic**: `claude-3-haiku-20240307` (default model)

Each provider implements `BaseAPIClient` interface with streaming support.

## Testing Utilities

The tool includes built-in command testing utilities:
```bash
# Test command execution
python main.py cmd test "git status"

# List allowed commands
python main.py cmd list

# Test template with commands
python main.py cmd template-test "Hello $(whoami)"
```

## Configuration Management

Key configuration files and patterns:
- `pyproject.toml` - Project metadata, dependencies, tool configuration
- `~/.prompts/config.json` - Runtime configuration and API keys
- `~/.prompts/*.yaml` - Individual prompt templates
- Tool settings support both CLI flags and persistent configuration