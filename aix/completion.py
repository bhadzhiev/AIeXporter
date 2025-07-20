"""
Autocompletion support for Typer CLI commands.
Provides dynamic completion for prompt names, variables, providers, and models.
"""

from typing import List
from .storage import PromptStorage
from .config import Config


def complete_prompt_names(incomplete: str) -> List[str]:
    """Complete prompt names from stored prompts."""
    try:
        storage = PromptStorage()
        prompts = storage.list_prompts()
        names = [prompt.name for prompt in prompts]

        # Filter by incomplete text
        if incomplete:
            names = [name for name in names if name.startswith(incomplete)]

        return names
    except Exception:
        return []


def complete_providers(incomplete: str) -> List[str]:
    """Complete API provider names including custom providers."""
    providers = ["openrouter", "openai", "anthropic"]

    # Add custom providers
    try:
        config = Config()
        custom_providers = config.get_custom_providers()
        custom_provider_names = [f"custom:{name}" for name in custom_providers.keys()]
        providers.extend(custom_provider_names)
    except Exception:
        pass  # Ignore errors and just return built-in providers

    if incomplete:
        providers = [p for p in providers if p.startswith(incomplete)]

    return providers


def complete_openrouter_models(incomplete: str) -> List[str]:
    """Complete OpenRouter model names."""
    models = [
        "meta-llama/llama-3.2-3b-instruct:free",
        "meta-llama/llama-3.2-1b-instruct:free",
        "meta-llama/llama-3.1-8b-instruct:free",
        "mistralai/mistral-7b-instruct:free",
        "microsoft/phi-3-mini-128k-instruct:free",
        "meta-llama/llama-3.1-70b-instruct",
        "meta-llama/llama-3.1-405b-instruct",
        "anthropic/claude-3-sonnet",
        "anthropic/claude-3-opus",
        "anthropic/claude-3-haiku",
        "openai/gpt-4",
        "openai/gpt-4-turbo",
        "openai/gpt-3.5-turbo",
        "google/gemini-pro",
        "mistralai/mistral-large",
        "cohere/command-r-plus",
    ]

    if incomplete:
        models = [m for m in models if m.startswith(incomplete)]

    return models


def complete_openai_models(incomplete: str) -> List[str]:
    """Complete OpenAI model names."""
    models = [
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4-0125-preview",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-0125",
    ]

    if incomplete:
        models = [m for m in models if m.startswith(incomplete)]

    return models


def complete_anthropic_models(incomplete: str) -> List[str]:
    """Complete Anthropic model names."""
    models = [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-2.1",
        "claude-2.0",
    ]

    if incomplete:
        models = [m for m in models if m.startswith(incomplete)]

    return models


def complete_models(incomplete: str) -> List[str]:
    """Complete model names - defaults to OpenRouter models."""
    # For simplicity, just return OpenRouter models by default
    # Users can override with --provider to get provider-specific models
    return complete_openrouter_models(incomplete)


def complete_prompt_variables(incomplete: str) -> List[str]:
    """Complete variable names in key=value format."""
    # For now, just return some common variable patterns
    # This could be enhanced to be context-aware in the future
    common_vars = [
        "language=",
        "code=",
        "file=",
        "project=",
        "description=",
        "input=",
        "output=",
        "type=",
        "format=",
        "style=",
    ]

    if incomplete:
        return [var for var in common_vars if var.startswith(incomplete)]

    return common_vars


def complete_config_keys(incomplete: str) -> List[str]:
    """Complete configuration key names."""
    keys = [
        "storage_path",
        "default_format",
        "editor",
        "auto_backup",
        "max_backups",
        "default_provider",
        "default_model",
        "openai_default_model",
        "anthropic_default_model",
        "streaming",
        "max_tokens",
        "temperature",
        "api_keys.openrouter",
        "api_keys.openai",
        "api_keys.anthropic",
    ]

    if incomplete:
        keys = [k for k in keys if k.startswith(incomplete)]

    return keys


def complete_tags(incomplete: str) -> List[str]:
    """Complete tag names from existing prompts."""
    try:
        storage = PromptStorage()
        prompts = storage.list_prompts()

        # Collect all unique tags
        all_tags = set()
        for prompt in prompts:
            if prompt.tags:
                all_tags.update(prompt.tags)

        tags = list(all_tags)

        if incomplete:
            tags = [tag for tag in tags if tag.startswith(incomplete)]

        return tags
    except Exception:
        return []


