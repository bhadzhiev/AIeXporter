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
pytest --cov=aix --cov-report=term-missing

# Type checking
mypy aix/

# Code formatting
black aix/
isort aix/

# Linting
flake8 aix/

# Pre-commit hooks (if configured)
pre-commit run --all-files
```

### Running the Tool
```bash
# Via installed CLI (package name: aix)
aix --help

# Development mode via main.py
python main.py --help

# Direct module execution
python -m aix.cli --help

# Common usage patterns
aix run my-prompt --param key=value           # Run with parameters
aix run my-prompt --dry-run                   # Preview without execution
aix run my-prompt --provider openai --model gpt-4  # Specify provider/model
aix run my-prompt --disable-commands          # Disable command execution
aix run my-prompt --output results.txt       # Save output to file
```

## Architecture

The codebase follows a modular, layered architecture:

### Core Components
- **CLI Layer**: `cli.py` - Main Typer-based CLI with rich console output
- **Template Engine**: `template.py` - Variable substitution and command execution
- **Storage Layer**: `storage.py` - File-based prompt persistence (YAML/JSON)
- **Collections**: `collection.py` - Template organization and collection management
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
- `$(command)` - Shell command execution (enabled by default, use `--disable-commands` to disable)
- `{cmd:command}` - Alternative command syntax
- `{exec:command}` - Explicit command execution syntax

### Security Model
- Command execution enabled by default with security restrictions
- Dangerous commands disabled by security patterns (see `command_executor.py`)
- 30-second timeout for all command execution  
- API keys stored securely in `~/.prompts/config.json`
- No command injection via template variables
- Use `--disable-commands` flag to disable command execution when needed

### Storage Architecture
- Prompts directory: `~/.prompts/`
- Metadata files: `{name}.yaml` or `{name}.json`
- Template content: `{name}.txt` (separate from metadata)
- Collections directory: `~/.prompts/collections/`
- Collection files: `collections/{name}.yaml` or `collections/{name}.json`
- Current collection tracking: `.current_collection` file
- Configuration: `config.json` in prompts directory

### API Provider Support
Built-in support for multiple AI providers with unified interface:
- **OpenRouter**: `meta-llama/llama-3.2-3b-instruct:free` (default, free tier)
- **OpenAI**: `gpt-3.5-turbo` (default model)
- **Anthropic**: `claude-3-haiku-20240307` (default model)
- **Custom Providers**: User-defined OpenAI-compatible endpoints

Each provider implements `BaseAPIClient` interface with streaming support.

### Custom Provider Support
Add custom API providers for any OpenAI-compatible endpoint:
```bash
# Add a custom provider (e.g., local Ollama)
aix provider add "ollama" "http://localhost:11434/v1" \
  --model "llama3.2" \
  --header "X-Custom-Header:value"

# List all custom providers
aix provider list

# Get provider details
aix provider info ollama

# Use custom provider
aix run my-prompt --provider custom:ollama

# Remove provider
aix provider remove ollama
```

Custom providers support:
- Custom base URLs for any OpenAI-compatible API
- Custom headers for authentication or API requirements
- Default model configuration per provider
- Bearer token or API key authentication
- Works with Ollama, vLLM, FastAPI, and other OpenAI-compatible services

See [docs/CUSTOM_PROVIDERS.md](docs/CUSTOM_PROVIDERS.md) for detailed documentation.

## Testing Utilities

The tool includes built-in command testing utilities:
```bash
# Test command execution
aix cmd test "git status"

# List allowed commands and security status
aix cmd list

# Test template with commands
aix cmd template-test "Hello $(whoami)"

# Test with custom timeout
aix cmd test "sleep 5" --timeout 10
```

## Utility Commands

### Template Safe Encoding
For complex templates with special characters, use safe encoding:
```bash
# Encode template with special characters for CLI safety
aix safe-template "Complex template with {vars} and $(commands)"
```

### Self-Upgrade
Keep aix updated with the built-in upgrade command:
```bash
# Upgrade to latest version from GitHub
aix upgrade

# Run with auto-upgrade (checks before execution)
aix run my-prompt --auto-upgrade
```

### Collection Migration
Migrate between collection formats:
```bash
# Migrate directory-based collections to XML format
aix collection-to-xml [collection-name]

# Migrate all collections to XML
aix collection-to-xml

# Legacy migration commands (for older formats)
aix collection-migrate [collection-name]
aix collection-xml-migrate [collection-name]
```

## Template Collections

aix supports organizing templates into collections for better workflow management.

### Collection Workflow
```bash
# Create a collection with templates
aix collection-create "web-dev" --description "Web development prompts" \
  --template code-review --template explain

# Load a collection as your working set
aix collection-load web-dev

# Work with collection templates
aix list                    # Shows only collection templates
aix run code-review         # Run templates from collection
aix collection-add new-template  # Add more templates

# Access all templates when needed
aix list --all              # Show all templates regardless of collection
aix collection-unload       # Return to working with all templates
```

### Collection Commands
- `collection-create <name>` - Create new collection with optional templates
- `collection-list` - Show all available collections and current status
- `collection-load <name>` - Load collection as current working set
- `collection-unload` - Clear current collection, work with all templates
- `collection-add <template>` - Add template to current collection
- `collection-remove <template>` - Remove template from current collection
- `collection-info [name]` - Show detailed collection information
- `collection-delete <name>` - Delete a collection
- `collection-export <name>` - Export collection to portable bundle
- `collection-import <path>` - Import collection from bundle

### Collection Import/Export

Collections can be exported as portable bundles and imported across different systems:

```bash
# Export a collection to a bundle
aix collection-export web-dev -o ~/backup/

# Import a collection bundle
aix collection-import ~/backup/web-dev-bundle.tar.gz

# Overwrite existing collection during import
aix collection-import ~/backup/web-dev-bundle.tar.gz --overwrite

# Export with specific format (yaml or json)
aix collection-export web-dev -f json -o ~/exports/
```

**Export Features**:
- **Complete Bundle**: Includes collection metadata and all template files
- **Placeholder Generators**: Preserves multi-language placeholder generators
- **Format Options**: Export as YAML (default) or JSON
- **Template Validation**: Only exports existing templates, reports missing ones
- **Manifest**: Includes export manifest with metadata and template inventory

**Import Features**:
- **Cross-Platform**: Bundles work across different systems
- **Conflict Detection**: Prevents overwriting existing collections without explicit flag
- **Template Recreation**: Recreates both XML and directory-based templates
- **Generator Preservation**: Maintains placeholder generators and all metadata

### Collection Features
- **Context-Aware Commands**: `list` and `run` commands are collection-aware
- **Template Validation**: Collections validate that referenced templates exist
- **Metadata Support**: Collections support descriptions, tags, and timestamps
- **Flexible Access**: Can bypass collection filtering with `--all` flag
- **Persistent State**: Current collection persists across CLI sessions

### Collection Storage
Collections are stored as metadata files in `~/.prompts/collections/`:
```yaml
name: web-dev
description: Web development prompts
templates:
  - code-review
  - explain
  - debug-helper
tags:
  - development
  - web
created_at: 2025-07-19T13:29:41.700001
updated_at: 2025-07-19T13:35:15.123456
```

## Multi-Language Placeholder Generators

Templates can include dynamic placeholder generators that execute scripts to provide real-time variable values:

### Supported Languages
- **Python**: Execute Python scripts for complex data processing
- **Bash**: Execute shell commands for system information

### Usage in Templates
```xml
<template>
  <metadata>
    <name>dynamic-analysis</name>
    <placeholder_generators>
      <placeholder_generator language="python"><![CDATA[
import glob
import os
placeholders = {
    "file_count": str(len(glob.glob("**/*.py", recursive=True))),
    "project_name": os.getcwd().split("/")[-1],
}
      ]]></placeholder_generator>
      <placeholder_generator language="bash"><![CDATA[
echo "git_branch=$(git branch --show-current 2>/dev/null || echo 'no-git')"
echo "git_status=$(git status --porcelain 2>/dev/null | wc -l)"
      ]]></placeholder_generator>
    </placeholder_generators>
  </metadata>
  <content><![CDATA[
Analyze {project_name} project:
- Files: {file_count}
- Branch: {git_branch}
- Changes: {git_status}
  ]]></content>
</template>
```

### Security Features
- **Python Sandbox**: Restricted globals and imports for safe execution
- **Bash Allowlist**: Only approved commands can be executed
- **Timeout Protection**: 30-second execution limit
- **Error Handling**: Graceful fallback when generators fail

### Generator Benefits
- **Real-time Data**: Automatically capture current system state
- **Dynamic Analysis**: Generate project-specific information on demand
- **Workflow Integration**: Seamlessly integrate with development tools
- **Template Reusability**: Same template works across different projects

## Configuration Management

Key configuration files and patterns:
- `pyproject.toml` - Project metadata, dependencies, tool configuration
- `~/.prompts/config.json` - Runtime configuration and API keys
- `~/.prompts/*.yaml` - Individual prompt templates
- `~/.prompts/collections/*.yaml` - Collection definitions
- `~/.prompts/.current_collection` - Current collection tracking
- Tool settings support both CLI flags and persistent configuration