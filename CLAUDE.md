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

# Update dependencies
make update                  # uv lock --upgrade && uv sync --group dev

# Clean build artifacts
make clean                   # removes build/, dist/, __pycache__
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
- **cli.py**: Typer-based CLI entry point with rich output and tab completion
- **api_client.py**: Factory pattern with BaseAPIClient interface for multiple AI providers
- **template.py**: Two-stage rendering (variables → commands → final prompt)
- **storage.py**: Collections-only storage system - all templates are stored within collections
- **collection.py**: XML-based collection management with embedded templates
- **commands/**: Command pattern implementation with security validation
  - **base.py**: Abstract Command interface and SecurityValidator
  - **executor.py**: Safe shell execution with allowlisting + 30s timeout
  - **security.py**: Default security patterns and validation logic
- **placeholder_generator.py**: Python/bash script execution for dynamic variables

### Key Patterns
- **Command Pattern**: Abstract `Command` interface for extensible command execution
- **Factory Pattern**: `get_client()` factory for API provider instantiation
- **Collections-Only Storage**: All templates must exist within collections, with a "default" collection for ungrouped items
- **Two-stage Template Rendering**: Variables first, then command execution, then final prompt
- **XML-Only Storage**: Unified XML format for all templates and collections
- **Security**: Regex-based command allowlisting with `SecurityValidator` interface
- **Providers**: Abstract `BaseAPIClient` with streaming support for multiple AI providers
- **Collections**: Template grouping via XML collections with embedded templates

### Configuration
- **Global**: `~/.prompts/config.json` (API keys, settings)
- **Collections**: `~/.prompts/collections/*.xml` (collections with embedded templates)
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
- `pyproject.toml`: Project metadata + tool configuration (requires Python 3.12+)
- `uv.lock`: Locked dependencies (use `uv sync`)
- `Makefile`: Development shortcuts for common tasks

## Important Implementation Details

### Command Execution Security
Commands are executed through a Command pattern with security validation:
- All shell commands must pass regex allowlisting via `SecurityValidator`
- 30-second timeout on all command execution
- Located in `aix/commands/` with base interfaces in `base.py`

### API Provider Architecture
Multiple AI providers supported through factory pattern:
- `BaseAPIClient` abstract interface in `api_client.py`
- Supported: OpenRouter, OpenAI, Anthropic, Groq, Together, Custom
- All providers support both sync and streaming generation
- Provider selection via `get_client()` factory function

### Template System
Two-stage rendering process for dynamic content:
1. Variable substitution (`{variable}` placeholders)
2. Command execution (if `--enable-commands` flag used)
3. Final prompt generation for AI provider

### Storage Architecture
XML-only unified storage system:
- **Individual Templates**: Single XML files (`{name}.xml`) containing all metadata and content
- **Collections**: XML files (`{collection}.xml`) with embedded templates and metadata
- **Template Structure**: Each XML template includes metadata, variables, tags, placeholder generators, and content in CDATA sections
- **Collection Structure**: Collections contain metadata and embedded template definitions
- **Benefits**: Single file format, embedded content, proper escaping via CDATA, simplified file management