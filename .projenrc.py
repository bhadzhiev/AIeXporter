#!/usr/bin/env python3
from projen.python import PythonProject

project = PythonProject(
    name="promptconsole",
    version="0.1.0",
    description="A comprehensive prompt management and execution tool",
    author_name="PromptConsole Team",
    author_email="team@promptconsole.dev",
    python_version="3.12",
    
    # Dependencies
    deps=[
        "httpx>=0.28.1",
        "pyyaml>=6.0.2",
        "rich>=14.0.0",
        "typer>=0.16.0",
    ],
    
    # Development dependencies
    dev_deps=[
        "pytest>=7.4.0",
        "pytest-cov>=4.1.0",
        "black>=23.0.0",
        "isort>=5.12.0",
        "flake8>=6.0.0",
        "mypy>=1.5.0",
        "pre-commit>=3.3.0",
    ],
    
    # Project structure
    module_name="promptconsole",
    
    # Scripts/entry points
    entrypoints={
        "promptconsole": "main:main",
        "pc": "main:main",
    },
    
    # Git configuration
    gitignore=[
        ".env",
        ".venv",
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".pytest_cache/",
        ".coverage",
        "htmlcov/",
        ".mypy_cache/",
        ".ruff_cache/",
        "dist/",
        "build/",
        "*.egg-info/",
        ".prompts/",
    ],
    
    # GitHub configuration
    github=True,
    github_options={
        "mergify": True,
        "workflows": [
            {
                "name": "CI",
                "on": {"push": {"branches": ["main"]}, "pull_request": {"branches": ["main"]}},
                "jobs": {
                    "test": {
                        "runs-on": "ubuntu-latest",
                        "steps": [
                            {"uses": "actions/checkout@v4"},
                            {"uses": "actions/setup-python@v4", "with": {"python-version": "3.12"}},
                            {"run": "pip install -e ."},
                            {"run": "pytest --cov=promptconsole tests/"},
                        ]
                    }
                }
            }
        ]
    },
    
    # Package manager
    package_manager="uv",
    
    # Additional configuration
    setuptools=True,
    venv=True,
    
    # License
    license="MIT",
    
    # Keywords
    keywords=["cli", "ai", "prompts", "automation", "development-tools"],
    
    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
        "Environment :: Console",
    ],
)

project.synth()