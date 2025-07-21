import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager."""
        if config_path:
            self.config_path = config_path
        else:
            # Check environment variable first for storage path
            env_path = os.environ.get("AIX_STORAGE_PATH")
            if env_path:
                self.config_path = Path(env_path) / "config.json"
            else:
                self.config_path = Path.home() / ".prompts" / "config.json"
        self.config_path.parent.mkdir(exist_ok=True)
        self._settings = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_path.exists():
            # Create default config
            default_config = {
                "storage_path": str(Path.home() / ".prompts"),
                "editor": "nano",
                "default_provider": "openrouter",
                "max_tokens": 1024,
                "temperature": 0.7,
                "auto_upgrade": False,
                "custom_providers": {},
                "commands_enabled": True,
                "disabled_commands": [],
            }
            self._save_config(default_config)
            return default_config

        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}


    def _save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file."""
        try:
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """Set a configuration value."""
        self._settings[key] = value
        return self._save_config(self._settings)

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self._settings.copy()

    def delete(self, key: str) -> bool:
        """Delete a configuration key."""
        if key in self._settings:
            del self._settings[key]
            return self._save_config(self._settings)
        return False

    def reset(self) -> bool:
        """Reset configuration to defaults."""
        if self.config_path.exists():
            self.config_path.unlink()
        self._settings = self._load_config()
        return True

    def get_storage_path(self) -> Path:
        """Get the configured storage path."""
        # Check environment variable first
        env_path = os.environ.get("AIX_STORAGE_PATH")
        if env_path:
            return Path(env_path)

        path_str = self.get("storage_path", str(Path.home() / ".prompts"))
        return Path(path_str)


    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a specific provider."""
        # Handle custom providers - check if API key is stored in custom_providers
        if provider.startswith("custom:"):
            provider_name = provider[7:]  # Remove "custom:" prefix
            custom_providers = self.get_custom_providers()
            if provider_name in custom_providers:
                custom_config = custom_providers[provider_name]
                if "api_key" in custom_config and custom_config["api_key"]:
                    return custom_config["api_key"]
        else:
            # For built-in providers, also check custom_providers
            custom_providers = self.get_custom_providers()
            if provider in custom_providers:
                custom_config = custom_providers[provider]
                if "api_key" in custom_config and custom_config["api_key"]:
                    return custom_config["api_key"]
        
        return None

    def set_api_key(self, provider: str, api_key: str) -> bool:
        """Set API key for a specific provider."""
        # Handle custom providers - store API key in custom_providers structure
        if provider.startswith("custom:"):
            provider_name = provider[7:]  # Remove "custom:" prefix
            custom_providers = self.get_custom_providers()
            if provider_name in custom_providers:
                custom_providers[provider_name]["api_key"] = api_key
                return self.set("custom_providers", custom_providers)
            else:
                # If custom provider doesn't exist, create it with minimal config
                custom_providers[provider_name] = {
                    "base_url": "",
                    "default_model": None,
                    "headers": {},
                    "auth_type": "bearer",
                    "api_key": api_key
                }
                return self.set("custom_providers", custom_providers)
        else:
            # For built-in providers, store in custom_providers structure
            custom_providers = self.get_custom_providers()
            if provider not in custom_providers:
                # Create custom provider entry for built-in provider
                custom_providers[provider] = {
                    "base_url": "",
                    "default_model": None,
                    "headers": {},
                    "auth_type": "bearer",
                    "api_key": api_key
                }
            else:
                custom_providers[provider]["api_key"] = api_key
            return self.set("custom_providers", custom_providers)

    def get_default_provider(self) -> str:
        """Get the default API provider."""
        return self.get("default_provider", "openrouter")

    def get_default_model(self, provider: str = None) -> str:
        """Get the default model for a provider."""
        if provider == "openai":
            return "gpt-3.5-turbo"
        elif provider == "anthropic":
            return "claude-3-haiku-20240307"
        else:  # openrouter or others
            return "microsoft/mai-ds-r1:free"

    def get_custom_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get all custom provider configurations."""
        return self.get("custom_providers", {})

    def add_custom_provider(
        self,
        name: str,
        base_url: str,
        default_model: str = None,
        headers: Dict[str, str] = None,
        auth_type: str = "bearer",
        api_key: str = None,
    ) -> bool:
        """Add a custom provider configuration."""
        custom_providers = self.get_custom_providers()
        
        # For built-in providers, preserve their correct base URLs
        built_in_urls = {
            "openrouter": "https://openrouter.ai/api/v1",
            "openai": "https://api.openai.com/v1", 
            "anthropic": "https://api.anthropic.com"
        }
        
        # If this is a built-in provider and an empty base_url was provided, use the correct one
        if name in built_in_urls and not base_url:
            base_url = built_in_urls[name]

        custom_providers[name] = {
            "base_url": base_url,
            "default_model": default_model,
            "headers": headers or {},
            "auth_type": auth_type,
            "api_key": api_key or "",
        }

        return self.set("custom_providers", custom_providers)

    def remove_custom_provider(self, name: str) -> bool:
        """Remove a custom provider configuration."""
        custom_providers = self.get_custom_providers()

        if name in custom_providers:
            del custom_providers[name]
            return self.set("custom_providers", custom_providers)

        return False

    def get_custom_provider(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific custom provider configuration."""
        custom_providers = self.get_custom_providers()
        return custom_providers.get(name)

    def get_commands_enabled(self) -> bool:
        """Get whether command execution is enabled by default."""
        return self.get("commands_enabled", True)

    def set_commands_enabled(self, enabled: bool) -> bool:
        """Set whether command execution is enabled by default."""
        return self.set("commands_enabled", enabled)

    def get_disabled_commands(self) -> list:
        """Get the list of disabled commands."""
        return self.get("disabled_commands", [])

    def set_disabled_commands(self, commands: list) -> bool:
        """Set the list of disabled commands."""
        return self.set("disabled_commands", commands)

    def add_disabled_command(self, command: str) -> bool:
        """Add a command to the disabled list."""
        disabled = self.get_disabled_commands()
        if command not in disabled:
            disabled.append(command)
            return self.set_disabled_commands(disabled)
        return True

    def remove_disabled_command(self, command: str) -> bool:
        """Remove a command from the disabled list."""
        disabled = self.get_disabled_commands()
        if command in disabled:
            disabled.remove(command)
            return self.set_disabled_commands(disabled)
        return False
