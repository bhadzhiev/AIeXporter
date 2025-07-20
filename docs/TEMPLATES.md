# Template Guide

## Template Variables

aix templates are like Mad Libs for AI. Fill in the blanks and watch the magic happen.

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

Templates are stored as XML files in `~/.prompts/`:

```xml
<!-- ~/.prompts/my-prompt.xml -->
<?xml version="1.0" encoding="utf-8"?>
<template>
  <metadata>
    <name>my-prompt</name>
    <description>Optional description</description>
    <variables>
      <variable>var1</variable>
      <variable>var2</variable>
    </variables>
    <tags>
      <tag>productivity</tag>
      <tag>development</tag>
    </tags>
    <created_at>2025-07-20T13:30:00.000000</created_at>
    <updated_at>2025-07-20T13:30:00.000000</updated_at>
  </metadata>
  <content><![CDATA[Your template here with {var1} and {var2}]]></content>
</template>
```

## Dynamic Placeholder Generators

Templates can include placeholder generators that execute scripts to provide real-time values:

### Python Generators
```xmltest 
<template>
  <metadata>
    <name>project-analysis</name>
    <placeholder_generators>
      <placeholder_generator language="python"><![CDATA[
import glob
import os
placeholders = {
    "file_count": str(len(glob.glob("**/*.py", recursive=True))),
    "project_name": os.getcwd().split("/")[-1],
    "large_files": str(len([f for f in glob.glob("**/*", recursive=True) 
                           if os.path.isfile(f) and os.path.getsize(f) > 1000000]))
}
      ]]></placeholder_generator>
    </placeholder_generators>
  </metadata>
  <content><![CDATA[
Analyze {project_name}:
- Python files: {file_count}
- Large files (>1MB): {large_files}
- Focus area: {focus_area}
  ]]></content>
</template>
```

### Bash Generators
```xml
<template>
  <metadata>
    <name>git-status-report</name>
    <placeholder_generators>
      <placeholder_generator language="bash"><![CDATA[
echo "current_branch=$(git branch --show-current 2>/dev/null || echo 'no-git')"
echo "uncommitted_changes=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
echo "last_commit=$(git log -1 --pretty='%h %s' 2>/dev/null || echo 'No commits')"
echo "repo_status=$(git status --porcelain 2>/dev/null && echo 'Changes detected' || echo 'Clean')"
      ]]></placeholder_generator>
    </placeholder_generators>
  </metadata>
  <content><![CDATA[
Git Status Report:
- Branch: {current_branch}
- Uncommitted: {uncommitted_changes} files
- Last commit: {last_commit}
- Status: {repo_status}
- Manual input: {user_notes}
  ]]></content>
</template>
```

### Combined Generators
```xml
<template>
  <metadata>
    <name>comprehensive-report</name>
    <placeholder_generators>
      <placeholder_generator language="python"><![CDATA[
import datetime
import os
placeholders = {
    "timestamp": datetime.datetime.now().isoformat(),
    "working_dir": os.getcwd(),
    "python_version": f"{sys.version_info.major}.{sys.version_info.minor}"
}
      ]]></placeholder_generator>
      <placeholder_generator language="bash"><![CDATA[
echo "hostname=$(hostname)"
echo "os_info=$(uname -s -r)"
echo "disk_usage=$(df -h . | tail -1 | awk '{print $5}')"
      ]]></placeholder_generator>
    </placeholder_generators>
  </metadata>
  <content><![CDATA[
System Report - {timestamp}
- Host: {hostname}
- OS: {os_info}
- Working Dir: {working_dir}
- Python: {python_version}
- Disk Usage: {disk_usage}
- Project: {project_name}
  ]]></content>
</template>
```

### Generator Security
- **Python Sandbox**: Restricted imports and globals
- **Bash Allowlist**: Only approved commands execute
- **Timeout Protection**: 30-second execution limit
- **Error Handling**: Graceful fallback on failure

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