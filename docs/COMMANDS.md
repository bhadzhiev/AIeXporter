# Command Reference

## Core Commands

### `aix create` - Create Prompts
```bash
# Basic creation
aix create name "template with {variable}"

# With description
aix create greet "Hello {name}!" --description "Greets a person"

# With tags
aix create code-review "Review {code}" --tags development,ai
```

### `aix run` - Run Prompts
```bash
# Basic run
aix run prompt-name --param key=value --execute

# With auto-upgrade
aix run prompt-name --auto-upgrade --execute

# Stream response
aix run prompt-name --stream --execute

# Save to file
aix run prompt-name --output result.txt --execute

# Generate weekly report with auto filename
aix run status-report --weekly-report --execute

# Command execution is enabled by default
aix run prompt-name --execute

# Disable command execution if needed
aix run prompt-name --disable-commands --execute
```

### `aix list` - List Prompts
```bash
# List all prompts
aix list

# List with details
aix list --verbose

# Filter by tag
aix list --tag development
```

### `aix edit` - Edit Prompts
```bash
# Edit with default editor
aix edit prompt-name

# Edit with specific editor
EDITOR=vim aix edit prompt-name
```

### `aix delete` - Delete Prompts
```bash
# Delete with confirmation
aix delete prompt-name

# Force delete
aix delete prompt-name --force
```

## Configuration Commands

### `aix config` - Configuration Management
```bash
# List all settings
aix config --list

# Set a value
aix config --set key value

# Get a value
aix config --get key

# Reset to defaults
aix config --reset

# Set API key
aix api-key openai
```

### `aix upgrade` - Self-Upgrade
```bash
# Upgrade to latest version
aix upgrade

# Upgrade happens automatically with --auto-upgrade
aix run prompt --auto-upgrade --execute
```

### `aix safe-template` - Template Encoding
```bash
# Encode complex template for CLI safety
aix safe-template "Template with {vars} and $(commands)"

# Use encoded output in create command
aix create my-prompt "$(aix safe-template 'Complex {template}')"
```

## Collection Commands

### `aix collection-create` - Create Collections
```bash
# Create empty collection
aix collection-create web-dev --description "Web development prompts"

# Create with templates
aix collection-create devops --template deploy --template monitor
```

### `aix collection-load` - Load Collections
```bash
# Load collection as current working set
aix collection-load web-dev

# Check current collection
aix collection-info
```

### `aix collection-add` - Add Templates to Collection
```bash
# Add template to current collection
aix collection-add new-template

# Must have a collection loaded first
aix collection-load web-dev
aix collection-add code-review
```

### `aix collection-export` - Export Collections
```bash
# Export to bundle
aix collection-export web-dev -o ~/backups/

# Export as JSON
aix collection-export web-dev -f json -o ~/exports/
```

### `aix collection-import` - Import Collections
```bash
# Import collection bundle
aix collection-import ~/backups/web-dev-bundle.tar.gz

# Overwrite existing
aix collection-import ~/backups/web-dev-bundle.tar.gz --overwrite
```

### `aix collection-import-repo` - Import Collections from GitHub
```bash
# Import collection from public GitHub repository
aix collection-import-repo https://github.com/user/collections-repo.git

# Import specific collection by name (required if repo has multiple collections)
aix collection-import-repo https://github.com/user/collections-repo.git --collection web-dev

# Overwrite existing collections
aix collection-import-repo https://github.com/user/collections-repo.git --overwrite

# Import with both specific collection and overwrite
aix collection-import-repo https://github.com/user/collections-repo.git --collection codecatalyst --overwrite

# Example: Import AWS CodeCatalyst templates
aix collection-import-repo https://github.com/bhadzhiev/AIeXpoerterCollections.git
```

### Collection Management Commands
```bash
# List all collections
aix collection-list

# Show collection info
aix collection-info [collection-name]

# Remove template from collection
aix collection-remove template-name

# Delete entire collection
aix collection-delete collection-name --force

# Unload current collection
aix collection-unload

# Migration commands
aix collection-to-xml [collection-name]
aix collection-migrate [collection-name]
```

## Provider Commands

### `aix provider` - Custom Provider Management
```bash
# Add custom provider
aix provider add ollama "http://localhost:11434/v1" --model "llama3.2"

# Add with authentication headers
aix provider add my-api "https://api.example.com/v1" \
  --model "custom-model" \
  --header "X-API-Key:secret"

# List custom providers
aix provider list

# Get provider details
aix provider info ollama

# Remove provider
aix provider remove ollama

# Use custom provider
aix run my-prompt --provider custom:ollama
```

## Command Testing

### `aix cmd` - Command Utilities
```bash
# Test a command
aix cmd test "git status"

# List available commands
aix cmd list

# Test template with commands
aix cmd template-test "Hello $(whoami)"
```

## Global Options

Most commands support these global options:
- `--help` - Show help
- `--version` - Show version

## Environment Variables

### `EDITOR`
Set default editor for `aix edit`:
```bash
export EDITOR=code
export EDITOR=nano
```

### `PROMPT_STORAGE_PATH`
Override default storage location:
```bash
export PROMPT_STORAGE_PATH="/custom/path"
```

## Command Aliases

Since aix can be run in multiple ways, you can use:
```bash
aix list
# or
python -m aix.cli list
```

## Command Chaining

Combine commands for powerful workflows:
```bash
# Create, test, then delete
aix create temp "test {input}" && aix run temp --param input="hello" --execute && aix delete temp --force

# Batch operations
aix list | grep "debug" | xargs -I {} aix delete {} --force
```

## Interactive Mode

When you're too lazy to remember flags:
```bash
# Missing variables will prompt for input
aix run greet --execute
# Prompt: name? > World

# Missing API key will prompt for setup
aix run prompt --execute
# Prompt: Set up OpenRouter API key? [y/N] > y
```

## Command Examples

### Daily Dev Workflow
```bash
# Morning standup summary
aix create standup "Generate standup summary for {project}: $(git log --oneline --since yesterday)"
aix run standup --param project="MyApp" --execute

# Code review
aix create review "Review this {language} change: $(git diff HEAD~1)"
aix run review --param language=python --execute

# Documentation
aix create doc "Document this function: {code}"
aix run doc --param code="$(cat my_function.py)" --execute
```

### System Administration
```bash
# System report
aix create sys-report "System status: $(uptime), $(df -h), $(free -h)"
aix run sys-report --execute

# Log analysis
aix create log-analyze "Analyze these logs: $(tail -100 /var/log/syslog)"
aix run log-analyze --execute
```

## Command Exit Codes

- `0` - Success
- `1` - General error
- `2` - Missing prompt/variable
- `3` - API error
- `4` - Configuration error

## Getting Help

```bash
# General help
aix --help

# Command-specific help
aix run --help
aix create --help
aix config --help
```