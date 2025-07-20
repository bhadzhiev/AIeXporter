## v0.12.0 (2025-07-20)

### Feat

- implement XML-based collections with embedded templates and system prompts

### Fix

- enable template resolution from XML collections in CLI run command

## v0.11.0 (2025-07-20)

### Feat

- enable --execute flag by default with toggle option

## v0.10.0 (2025-07-20)

### Feat

- enhance CustomAPIClient to support different authentication types

## v0.9.1 (2025-07-20)

### Fix

- correct typo in CHANGELOG.md (Commands → Command)

## v0.9.0 (2025-07-20)

### Feat

- implement CDATA for XML template content and fix character escaping

## v0.8.1 (2025-07-20)

### Fix

- improve command security pattern matching precision

## v0.8.0 (2025-07-20)

### BREAKING CHANGE
 
- Command are now enabled by default, --enable-commands replaced with --disable-commands

### Feat 

- enable command execution by default with security restrictions

## v0.7.0 (2025-07-20)

### BREAKING CHANGE

- Remove YAML+TXT format support, XML and directories are now the only supported formats

### Feat

- default to XML templates and directory-based collections

## v0.6.2 (2025-07-20)

### Fix

- resolve variable name collision in command output display

## v0.6.1 (2025-07-20)

### Fix

- configure commitizen to auto-sync __init__.py version

## v0.6.0 (2025-07-20)

### Feat

- add intelligent command execution with smart fallbacks

## v0.5.3 (2025-07-20)

### Fix

- improve CustomAPIClient error handling and robustness

## v0.5.2 (2025-07-20)

### Fix

- remove flawed version check in upgrade command

## v0.5.1 (2025-07-20)

### Fix

- add custom provider support to api-key command

## v0.5.0 (2025-07-19)

### Feat

- add custom API provider support

## v0.4.0 (2025-07-19)

### Feat

- enhance documentation with automated GitHub release creation

## v0.3.1 (2025-07-19)

### Fix

- sync __init__.py version with pyproject.toml (0.3.0)

## v0.3.0 (2025-07-19)

### Feat

- implement automated version bumping with pre-push git hook

## v0.2.14 (2025-07-19)

### Feat

- add comprehensive test suite with 103 tests and 53% coverage
- implement AIX_STORAGE_PATH environment variable support for testing
- add pre-push git hook for automatic version bumping with commitizen
- always show generated prompt before API execution
- implement collection import/export functionality
- implement comprehensive template collections feature
- show 'already up to date' message when no upgrade is needed
- display version after successful upgrade command

### Fix

- fix deprecation warning in tar extraction by adding data_filter for Python 3.12+
- fix all failing CLI integration tests (7 failed → 0 failed)
- fix collection directory creation with proper parent directory handling
- correct repository URLs in documentation from prompt.git to AIeXporter.git
- update git pre-commit hook to handle missing setup.py
- update upgrade messages to use 'aix' branding consistently
- sync __init__.py version with pyproject.toml (0.2.2)
- update __init__.py version to match pyproject.toml (0.2.1)

### Test

- add comprehensive CLI integration test suite
- fix string matching issues in test assertions
- improve test isolation with proper environment variable handling
- add test coverage for all core functionality

### Refactor

- reorganize repository structure and clean up legacy files

### Chore

- update development dependencies (pytest, black, isort, flake8, mypy)
- add development tools configuration in pyproject.toml

## v0.2.1 (2025-07-19)

### Fix

- sync __init__.py version with pyproject.toml (0.2.0)

## v0.2.0 (2025-07-19)

### Feat

- add IDE files and prompts directory to gitignore

## v0.1.0 (2025-07-19)

### Feat

- add commitizen for semantic versioning and changelog management
- implement all missing CLI commands and enhance existing functionality
- add auto-upgrade functionality to run command
- add self-upgrade command via aix upgrade
- rename project to 'aix' - AI executor
- complete distribution setup with UV, GitHub Actions, and PyPI publishing
- Initial release of PromptConsole - AI-powered CLI prompt management tool

### Fix

- use system uv binary for upgrade command
- improve upgrade command for uv tool installations
- correct entry point for CLI commands
- correct UV tool install syntax

### Refactor

- rename promptconsole package to aix for consistent branding
