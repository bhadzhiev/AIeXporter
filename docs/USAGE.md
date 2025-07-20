# Usage Guide

## Quick Start

```bash
# Create your first prompt
aix create greet "Hello {name}! Welcome to $(hostname)"

# Run it
aix run greet --param name=World --execute

# List all prompts
aix list
```

## Advanced Usage

### Template Magic

aix supports multiple types of template variables:

1. **Simple variables**: `{variable}`
2. **Command execution**: `$(command)`
3. **Explicit commands**: `{exec:command}`

### Examples

```bash
# Create a prompt that summarizes your git log
aix create git-summary "Summarize these git commits: $(git log --oneline -10)"

# Create a prompt with dynamic system info
aix create sys-info "Current system: $(uname -a). Disk usage: $(df -h | grep '^/')"

# Run with parameters
aix run git-summary --execute
aix run sys-info --execute
```

### Command Execution Safety

Command execution is enabled by default but restricted by security patterns. Use `--disable-commands` to disable it:

```bash
# Commands enabled by default
aix run my-prompt --execute

# Disable commands if needed
aix run my-prompt --execute --disable-commands
```

## Auto-Upgrade Magic

Never manually upgrade again:

```bash
# One-time upgrade
aix run my-prompt --auto-upgrade --execute

# Always upgrade (set in config)
aix config --set auto_upgrade true
```

## API Provider Switching

```bash
# Use specific provider
aix run my-prompt --provider openai --execute
aix run my-prompt --provider anthropic --execute

# Set default provider
aix config --set default_provider openai
```

## Streaming Responses

For those who like watching paint dry:

```bash
aix run my-prompt --stream --execute
```

## Output to File

```bash
aix run my-prompt --output response.txt --execute
```

## Collection Workflow

Organize your templates into collections for better project management:

### Basic Collection Usage

```bash
# Create a collection
aix collection-create webdev --description "Web development templates"

# Load the collection
aix collection-load webdev

# Add templates to collection
aix collection-add code-review
aix collection-add bug-report
aix collection-add deploy-checklist

# Work with collection templates
aix list                    # Shows only webdev templates
aix run code-review         # Runs template from collection

# Export for sharing
aix collection-export webdev -o ~/backups/

# Import shared collection
aix collection-import ~/shared/frontend-bundle.tar.gz
```

### Collection Features

- **Context-Aware**: `list` and `run` commands work within collection scope
- **Persistent State**: Current collection persists across sessions
- **Portable**: Export/import collections as bundles
- **Flexible**: Use `--all` flag to bypass collection filtering

## Dynamic Placeholder Generators

Create templates that generate real-time data automatically:

### Python Generators

```bash
# Create template with Python generator
aix create project-stats "
Project Analysis:
- Files: {file_count}
- Project: {project_name}
- Large files: {large_files}
- Notes: {notes}
"

# The template automatically includes Python code to generate:
# - file_count: Number of Python files
# - project_name: Current directory name  
# - large_files: Number of files > 1MB
```

### Bash Generators

```bash
# Create template with Git information
aix create git-report "
Git Status:
- Branch: {current_branch}
- Changes: {uncommitted_changes} files
- Last commit: {last_commit}
- Manual notes: {notes}
"

# Automatically generates git status information
```

### Generator Benefits

- **Real-time Data**: Always current system information
- **No Manual Updates**: Generators run automatically
- **Cross-Platform**: Same template works everywhere
- **Secure**: Sandboxed execution with timeouts

## Custom Providers

Use local or custom AI models:

```bash
# Add Ollama (local models)
aix provider add ollama "http://localhost:11434/v1" --model "llama3.2"

# Use custom provider
aix run my-prompt --provider custom:ollama

# Add any OpenAI-compatible service
aix provider add my-api "https://api.example.com/v1" \
  --model "custom-model" \
  --header "X-API-Key:secret"
```

## Tips and Tricks

### Dry Run Everything
```bash
# Preview generated prompt without API call
aix run my-prompt --dry-run --param name=test
```

### Parameter Files
```bash
# Use file for complex parameters
echo "code=$(cat my_script.py)" > params.txt
aix run code-review --param-file params.txt --execute
```

### Template Debugging
```bash
# Test command execution
aix cmd test "git status"

# Test templates
aix cmd template-test "Hello $(whoami)"
```

### Workflow Automation
```bash
# Morning standup
aix run standup --param project="MyApp" --execute

# Code review workflow  
aix run code-review --param file="src/main.py" --execute

# Deploy checklist
aix run deploy-check --param environment="staging" --execute
```