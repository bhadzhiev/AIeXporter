#!/usr/bin/env python3
"""
Projen configuration for uv-based Python project.
This creates the basic project structure without managing dependencies.
"""

import os
import json
from pathlib import Path

# Create minimal project structure
project_root = Path(__file__).parent

# Create pyproject.toml for uv
pyproject_content = '''[build-system]
requires = ["setuptools>=61", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "promptconsole"
version = "0.1.0"
description = "A comprehensive prompt management and execution tool"
readme = "README.md"
requires-python = ">=3.12"
authors = [
    {name = "PromptConsole Team", email = "team@promptconsole.dev"}
]
license = {text = "MIT"}
keywords = ["cli", "ai", "prompts", "automation", "development-tools"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Utilities",
    "Environment :: Console",
]
dependencies = [
    "httpx>=0.28.1",
    "pyyaml>=6.0.2",
    "rich>=14.0.0",
    "typer>=0.16.0",
]

[project.scripts]
promptconsole = "main:main"
pc = "main:main"

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "flake8>=6.0.0",
    "mypy>=1.5.0",
    "pre-commit>=3.3.0",
]

[tool.black]
line-length = 88
target-version = ["py312"]

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
addopts = "--cov=promptconsole --cov-report=term-missing"
'''

# Write pyproject.toml
with open(project_root / "pyproject.toml", "w") as f:
    f.write(pyproject_content)

# Create .gitignore
with open(project_root / ".gitignore", "a") as f:
    f.write("""
# UV specific
.uv/
uv.lock
""")

print("✅ UV-compatible project configuration created!")
print("Run: uv sync")
print("Run: uv add package-name")
print("Run: uv run pytest")