# Template Guide

**NEW**: aix now uses collections-only XML storage! All templates are automatically organized in collections with XML format. Templates are embedded within collection files for better organization and no loose files.

## Template Variables

aix templates are like Mad Libs for AI. Fill in the blanks and watch the magic happen.

### Basic Variables

**Note**: Examples below show the template structure. In the new collections-only system, templates are automatically embedded in XML collections, but you create them using the same `aix create` command.

```bash
# Create template (automatically stored in collections)
aix create story "Write a {genre} story about {character} who {action}"
```

```bash
aix run story --param genre=sci-fi --param character="Captain Obvious" --param action="saves the day with common sense"
```

### Command Execution

Want to include live system data? We've got you covered:

```bash
# Create template with commands (stored in XML collections automatically)
aix create sys-report "System Report for \$(hostname)

CPU: \$(lscpu | grep 'Model name' | cut -d: -f2 | xargs)
Memory: \$(free -h | grep '^Mem:' | awk '{print \$2}')
Disk: \$(df -h / | tail -1 | awk '{print \$4}' | sed 's/G/ GB/')

Current user: \$(whoami)
Current directory: \$(pwd)
Git status: \$(git status --porcelain | wc -l) modified files"

# Run with debug to see what commands were executed
aix run sys-report --debug
```

### Advanced Command Syntax

```bash
# Create template with explicit command syntax
aix create git-ai "Analyze these git changes and suggest a commit message:

\`\`\`diff
{exec:git diff --cached}
\`\`\`

Changes include {exec:git diff --cached --name-only | wc -l} files."

# Run with streaming (default) and debug mode
aix run git-ai --debug
```

### Environment Variables

```bash
# Create template with environment variables
aix create env-aware "Hello {name}! You're running this on {exec:echo \$OSTYPE}.
Your shell is {exec:echo \$SHELL}.
The current time is {exec:date}."

# Run with parameter
aix run env-aware --param name="Developer"
```

### Multi-line Templates

```bash
# Create multi-line template for code review
aix create code-review "Review this code change:

**File**: {filename}
**Language**: {language}
**Changes**:
\`\`\`{language}
{exec:git diff HEAD~1..HEAD -- {filename}}
\`\`\`

Please provide:
1. Summary of changes
2. Potential issues
3. Suggestions for improvement"

# Run the template
aix run code-review --param filename="src/main.py" --param language="python"
```

## Collections-Only Storage

All templates are now automatically stored in XML collections with embedded template content. This provides:

- **Better Organization**: Templates are grouped in meaningful collections
- **No Loose Files**: Everything is organized and structured
- **XML Format**: Consistent storage with metadata preservation
- **Default Collection**: Ungrouped templates go to a "default" collection automatically

```bash
# Create templates (automatically stored in default collection)
aix create my-template "Hello {name}!"

# Create collections for organization
aix collection-create web-dev --description "Web development templates"

# Add templates to specific collections
aix collection-add my-template

# Work within collection context
aix collection-load web-dev
aix list  # Shows only web-dev templates
```

## Template Best Practices

### 1. Make Variables Obvious

```bash
# Good: Clear variable names
aix create feature-request "Create a feature request for {project_name}: {feature_description}"

# Bad: Unclear variable names  
aix create feature-request "Create a feature request for {p}: {d}"
```

### 2. Use Debug Mode for Development

```bash
# Use debug mode to see what's happening during template execution
aix run my-template --debug --param topic="AI tools"

# Debug mode shows:
# - Generated prompt before API execution
# - Command outputs that were executed
# - Any placeholder generator results
```

### 3. Combine Variables and Commands

```bash
# Create template combining variables and live system data
aix create project-summary "Project {project_name} Summary:

Project: {project_name}
Files: {exec:find {project_path} -type f | wc -l}
Git Status: {exec:cd {project_path} && git status --porcelain | wc -l} modified files
Last Commit: {exec:cd {project_path} && git log -1 --pretty=%s}"

# Run with both variables and commands
aix run project-summary --param project_name="MyApp" --param project_path="/path/to/project"
```

## Template Storage

Templates are now stored embedded within XML collection files in `~/.prompts/collections/`. This provides better organization and no loose files.

```xml
<!-- ~/.prompts/collections/default.xml -->
<?xml version="1.0" encoding="utf-8"?>
<collection>
  <metadata>
    <name>default</name>
    <description>Default collection for ungrouped templates</description>
    <created_at>2025-07-21T12:00:00.000000</created_at>
    <updated_at>2025-07-21T12:00:00.000000</updated_at>
  </metadata>
  <templates>
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
        <created_at>2025-07-21T12:00:00.000000</created_at>
        <updated_at>2025-07-21T12:00:00.000000</updated_at>
      </metadata>
      <content><![CDATA[Your template here with {var1} and {var2}]]></content>
    </template>
  </templates>
</collection>
```

### Storage Benefits

- **Organized**: Templates grouped in meaningful collections
- **XML Format**: Consistent structure with CDATA for content
- **Embedded**: No separate content/metadata files
- **Collections-Only**: Everything is organized, no loose files

## Dynamic Placeholder Generators

Templates can include placeholder generators that execute scripts to provide real-time values:

### Python Generators
```xml
<template>
  <metadata>
    <name>project-analysis</name>
    <placeholder_generators>
      <placeholder_generator language="python"><![CDATA[
import glob
import os
import sys
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

## Template Examples (XML Collections)

Templates are now stored in XML collections with embedded content. Here are examples showing the XML structure:

### 1. Git Commit Message Generator

```xml
<template>
  <metadata>
    <name>commit-msg</name>
    <description>Generate git commit messages from staged changes</description>
    <variables />
    <tags>
      <tag>git</tag>
      <tag>development</tag>
    </tags>
  </metadata>
  <content><![CDATA[
Generate a concise git commit message for these changes:

{exec:git diff --cached}

Format: <type>: <description>
Types: feat, fix, docs, style, refactor, test, chore
  ]]></content>
</template>
```

### 2. Code Documentation (Language Specific)

```xml
<template>
  <metadata>
    <name>doc-code</name>
    <description>Generate documentation for code functions</description>
    <variables>
      <variable>language</variable>
      <variable>code</variable>
    </variables>
    <tags>
      <tag>documentation</tag>
      <tag>code-review</tag>
    </tags>
  </metadata>
  <content><![CDATA[
Document this {language} function:

```{language}
{code}
```

Include:
- Purpose
- Parameters
- Return value
- Examples
  ]]></content>
</template>
```

### 3. Python Project Analysis

```xml
<template>
  <metadata>
    <name>analyze-python</name>
    <description>Analyze Python project structure and dependencies</description>
    <variables>
      <variable>project_path</variable>
    </variables>
    <tags>
      <tag>python</tag>
      <tag>analysis</tag>
    </tags>
  </metadata>
  <content><![CDATA[
Analyze this Python project located at {project_path}:

Project Structure:
{exec:find {project_path} -name "*.py" -type f | head -10}

Dependencies:
{exec:cd {project_path} && grep -h "^import\|^from" **/*.py | sort -u | head -10}

File Count:
{exec:find {project_path} -name "*.py" | wc -l} Python files

Main Entry Point:
{exec:find {project_path} -name "main.py" -o -name "__main__.py" | head -1}
  ]]></content>
</template>
```

### 4. Bash Script Analysis

```xml
<template>
  <metadata>
    <name>analyze-bash</name>
    <description>Analyze bash scripts for security and best practices</description>
    <variables>
      <variable>script_path</variable>
    </variables>
    <tags>
      <tag>bash</tag>
      <tag>security</tag>
    </tags>
  </metadata>
  <content><![CDATA[
Analyze this bash script: {script_path}

Script content:
```bash
{exec:cat {script_path}}
```

Permissions: {exec:ls -la {script_path} | awk '{print $1}'}
Shebang: {exec:head -1 {script_path}}
Line count: {exec:wc -l < {script_path}}
  ]]></content>
</template>
```

### 5. Meeting Summary

```xml
<template>
  <metadata>
    <name>meeting-summary</name>
    <description>Generate structured meeting summaries</description>
    <variables>
      <variable>meeting_title</variable>
      <variable>attendees</variable>
      <variable>transcript</variable>
    </variables>
    <tags>
      <tag>meeting</tag>
      <tag>summary</tag>
    </tags>
  </metadata>
  <content><![CDATA[
Create a meeting summary:

**Meeting**: {meeting_title}
**Date**: {exec:date +%Y-%m-%d}
**Attendees**: {attendees}

**Transcript**:
{transcript}

**Summary**:
  ]]></content>
</template>
```