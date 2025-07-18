import json
from pathlib import Path
from typing import Any, Dict, Optional

class Config:
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager."""
        self.config_path = config_path or Path.home() / ".prompts" / "config.json"
        self.config_path.parent.mkdir(exist_ok=True)
        self._settings = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_path.exists():
            # Create default config
            default_config = {
                "storage_path": str(Path.home() / ".prompts"),
                "default_format": "yaml",
                "editor": "nano",
                "auto_backup": True,
                "max_backups": 5,
                "default_provider": "openrouter",
                "default_model": "meta-llama/llama-3.2-3b-instruct:free",
                "api_keys": {},
                "streaming": False,
                "max_tokens": 1024,
                "temperature": 0.7
            }
            self._save_config(default_config)
            return default_config
        
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    
    def _save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
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
        path_str = self.get("storage_path", str(Path.home() / ".prompts"))
        return Path(path_str)
    
    def get_default_format(self) -> str:
        """Get the default file format for new prompts."""
        return self.get("default_format", "yaml")
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a specific provider."""
        api_keys = self.get("api_keys", {})
        return api_keys.get(provider)
    
    def set_api_key(self, provider: str, api_key: str) -> bool:
        """Set API key for a specific provider."""
        api_keys = self.get("api_keys", {})
        api_keys[provider] = api_key
        return self.set("api_keys", api_keys)
    
    def get_default_provider(self) -> str:
        """Get the default API provider."""
        return self.get("default_provider", "openrouter")
    
    def get_default_model(self, provider: str = None) -> str:
        """Get the default model for a provider."""
        if provider == "openai":
            return self.get("openai_default_model", "gpt-3.5-turbo")
        elif provider == "anthropic":
            return self.get("anthropic_default_model", "claude-3-haiku-20240307")
        else:  # openrouter or others
            return self.get("default_model", "meta-llama/llama-3.2-3b-instruct:free")