# Usage Guide

## Quick Start

```bash
# Create your first prompt
aix create greet "Hello {name}! Welcome to $(hostname)"

# Run it (streaming enabled by default!)
aix run greet --param name=World

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

# Run with parameters (streaming by default)
aix run git-summary
aix run sys-info
```

### Command Execution Safety

Command execution is enabled by default but restricted by security patterns. Use `--disable-commands` to disable it:

```bash
# Commands enabled by default, streaming enabled by default
aix run my-prompt

# Disable commands if needed
aix run my-prompt --disable-commands

# Debug mode shows what commands were executed
aix run my-prompt --debug
```

## Auto-Upgrade Magic

Never manually upgrade again:

```bash
# One-time upgrade
aix run my-prompt --auto-upgrade

# Always upgrade (set in config)
aix config --set auto_upgrade true
```

## API Provider Switching

```bash
# Use specific provider
aix run my-prompt --provider openai
aix run my-prompt --provider anthropic

# Set default provider
aix config --set default_provider openai
```

## Streaming Responses

Streaming is now enabled by default! For those who like instant gratification:

```bash
aix run my-prompt              # Streaming on by default
aix run my-prompt --no-stream  # Turn off streaming if needed
```

## Debug Mode

See what's happening under the hood:

```bash
aix run my-prompt --debug      # Shows generated prompts and command outputs
```

## Output to File

```bash
aix run my-prompt --output response.txt
```

## Collection Workflow

**NEW**: aix now uses collections-only storage! All templates are automatically organized in XML collections. No more loose files - everything is structured and organized.

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

# Import collections from GitHub repositories
aix collection-import-repo https://github.com/user/collections-repo.git
```

### Collection Features

- **Context-Aware**: `list` and `run` commands work within collection scope
- **Persistent State**: Current collection persists across sessions
- **Portable**: Export/import collections as bundles
- **GitHub Integration**: Import collections directly from public repositories
- **Flexible**: Use `--all` flag to bypass collection filtering

### Sharing Collections via GitHub

Share your collections with the community or across teams using GitHub repositories:

```bash
# Import public collections (great for getting started!)
aix collection-import-repo https://github.com/bhadzhiev/AIeXpoerterCollections.git

# Import specific collection when repo has multiple
aix collection-import-repo https://github.com/user/collections.git --collection web-dev

# Overwrite existing collections during updates
aix collection-import-repo https://github.com/user/collections.git --overwrite
```

**Repository Structure**: Create a public GitHub repo with this structure:
```
your-collections-repo/
└── collections/
    ├── web-dev.xml
    ├── devops.xml
    └── data-science.xml
```

Each XML file contains a complete collection with embedded templates, making sharing incredibly simple!

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

# Use custom provider (note the custom: prefix)
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
# Morning standup (debug mode shows what data was collected)
aix run standup --param project="MyApp" --debug

# Code review workflow (streaming by default)
aix run code-review --param file="src/main.py"

# Deploy checklist
aix run deploy-check --param environment="staging"
```