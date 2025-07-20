# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Response Style
- Provide concise, text-only responses
- No images, borders, or decorative formatting
- Use plain text for all output

## Project Overview

**aix** (AI eXecutor) is a CLI tool for managing and executing AI prompts with dynamic variables, command execution, and multi-provider support.

## Development Commands

### Setup & Installation
```bash
# Development setup (recommended)
uv sync

# Alternative with pip
pip install -e ".[dev]"
```

### Testing & Quality
```bash
# Run all tests
make test                    # or: uv run pytest

# Run with coverage
pytest --cov=aix --cov-report=term-missing

# Code quality checks
make lint                    # uv run ruff check .
make fmt                     # uv run ruff format .
make type                    # uv run mypy aix/

# Single test file
pytest tests/test_api_client.py -v
```

### Running the Tool
```bash
# Development mode
python main.py --help
python -m aix.cli --help

# Installed CLI
aix --help

# Common usage
aix run prompt-name --param key=value --execute
aix create prompt-name "template with {variables}"
aix collection-create web-dev --template code-review
```

## Architecture

### Core Components
- **cli.py**: Typer-based CLI entry point with rich output
- **api_client.py**: Factory pattern for OpenRouter/OpenAI/Anthropic providers
- **template.py**: Two-stage rendering (variables → commands → final prompt)
- **storage.py**: YAML/JSON file persistence, separate content/metadata storage
- **collection.py**: Template grouping and workspace management
- **command_executor.py**: Safe shell execution with allowlisting + 30s timeout
- **placeholder_generator.py**: Python/bash script execution for dynamic variables

### Key Patterns
- **Storage**: `{name}.yaml` + `{name}.txt` in `~/.prompts/`
- **Security**: Command allowlisting via regex patterns
- **Providers**: `BaseAPIClient` interface with streaming support
- **Collections**: `~/.prompts/collections/{name}.yaml` for template grouping

### Configuration
- **Global**: `~/.prompts/config.json` (API keys, settings)
- **Templates**: `~/.prompts/*.yaml` + `~/.prompts/*.txt`
- **Collections**: `~/.prompts/collections/*.yaml`
- **Current collection**: `~/.prompts/.current_collection`

## Key Files

### Entry Points
- `main.py`: Development entry point
- `aix/cli.py`: CLI interface with all commands
- `aix/__init__.py`: Package initialization

### Testing
- `tests/conftest.py`: Shared test fixtures
- `tests/test_*.py`: Unit tests for each module
- `pytest` with coverage reporting configured

### Build & Dependencies
- `pyproject.toml`: Project metadata + tool configuration
- `Makefile`: Development shortcuts
- `uv.lock`: Locked dependencies (use `uv sync`)