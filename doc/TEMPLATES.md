# Template Guide

## Template Variables

PromptConsole templates are like Mad Libs for AI. Fill in the blanks and watch the magic happen.

### Basic Variables

```yaml
# prompt.yaml
template: "Write a {genre} story about {character} who {action}"
variables:
  - genre
  - character
  - action
```

```bash
aix run story --param genre=sci-fi --param character="Captain Obvious" --param action="saves the day with common sense" --execute
```

### Command Execution

Want to include live system data? We've got you covered:

```yaml
# sys-report.yaml
template: |
  System Report for $(hostname)
  
  CPU: $(lscpu | grep 'Model name' | cut -d: -f2 | xargs)
  Memory: $(free -h | grep '^Mem:' | awk '{print $2}')
  Disk: $(df -h / | tail -1 | awk '{print $4}' | sed 's/G/ GB/')
  
  Current user: $(whoami)
  Current directory: $(pwd)
  Git status: $(git status --porcelain | wc -l) modified files
```

### Advanced Command Syntax

```yaml
# git-ai.yaml
template: |
  Analyze these git changes and suggest a commit message:
  
  ```diff
  {exec:git diff --cached}
  ```
  
  Changes include {exec:git diff --cached --name-only | wc -l} files.
```

### Environment Variables

```yaml
# env-aware.yaml
template: |
  Hello {name}! You're running this on {exec:echo $OSTYPE}.
  Your shell is {exec:echo $SHELL}.
  The current time is {exec:date}.
```

### Multi-line Templates

```yaml
# code-review.yaml
template: |
  Review this code change:
  
  **File**: {filename}
  **Language**: {language}
  **Changes**:
  ```{language}
  {exec:git diff HEAD~1..HEAD -- {filename}}
  ```
  
  Please provide:
  1. Summary of changes
  2. Potential issues
  3. Suggestions for improvement
variables:
  - filename
  - language
```

## Template Best Practices

### 1. Make Variables Obvious

```yaml
# Good
variables:
  - project_name
  - feature_description

# Bad
variables:
  - p
  - d
```

### 2. Use Default Values

```yaml
# In your prompt file
template: "Create a {type:-blog post} about {topic}"
```

### 3. Combine Variables and Commands

```yaml
# project-summary.yaml
template: |
  Project: {project_name}
  
  Files: {exec:find {project_path} -type f | wc -l}
  Languages: {exec:find {project_path} -name '*.py' | wc -l} Python files
  Last commit: {exec:cd {project_path} && git log -1 --pretty="%s"}
variables:
  - project_name
  - project_path
```

## Template Storage

Templates are stored as YAML files in `~/.prompts/`:

```yaml
# ~/.prompts/my-prompt.yaml
name: my-prompt
template: "Your template here"
variables:
  - var1
  - var2
description: "Optional description"
tags:
  - productivity
  - development
```

## Template Examples

### 1. Git Commit Message Generator

```yaml
# commit-msg.yaml
name: commit-msg
template: |
  Generate a concise git commit message for these changes:
  
  {exec:git diff --cached}
  
  Format: <type>: <description>
  Types: feat, fix, docs, style, refactor, test, chore
variables: []
```

### 2. Code Documentation

```yaml
# doc-code.yaml
name: doc-code
template: |
  Document this {language} function:
  
  ```{language}
  {code}
  ```
  
  Include:
  - Purpose
  - Parameters
  - Return value
  - Examples
variables:
  - language
  - code
```

### 3. Meeting Summary

```yaml
# meeting-summary.yaml
name: meeting-summary
template: |
  Create a meeting summary:
  
  **Meeting**: {meeting_title}
  **Date**: {exec:date +%Y-%m-%d}
  **Attendees**: {attendees}
  
  **Transcript**:
  {transcript}
  
  **Summary**:
variables:
  - meeting_title
  - attendees
  - transcript
```