## v0.2.2 (2025-07-19)

### Fix

- update __init__.py version to match pyproject.toml (0.2.1)

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
