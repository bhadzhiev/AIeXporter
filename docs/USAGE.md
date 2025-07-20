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

PromptConsole supports three types of template variables:

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