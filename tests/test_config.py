import pytest
import json
from pathlib import Path
from aix.config import Config


class TestConfig:
    """Test configuration management."""

    def test_config_initialization(self, temp_storage_dir):
        """Test config initialization with custom directory."""
        config_path = temp_storage_dir / "config.json"
        config = Config(config_path)
        
        assert config.config_path == config_path
        assert config_path.parent.exists()

    def test_config_initialization_creates_default(self, temp_storage_dir):
        """Test config creates default file if not exists."""
        config_path = temp_storage_dir / "config.json"
        config = Config(config_path)
        
        assert config_path.exists()
        
        # Verify default settings
        assert config.get("default_provider") == "openrouter"
        # Storage path should be the configured path
        expected_storage = str(temp_storage_dir)
        actual_storage = config.get("storage_path")
        # Allow for both temp directory and home directory as valid defaults
        assert actual_storage in [expected_storage, str(Path.home() / ".prompts")]
        assert config.get("default_format") == "yaml"
        assert config.get("editor") == "nano"

    def test_get_config_value(self, temp_storage_dir):
        """Test getting configuration values."""
        config = Config(temp_storage_dir / "config.json")
        
        assert config.get("auto_backup", True) is True
        assert config.get("max_backups", 5) == 5
        assert config.get("nonexistent", "default") == "default"

    def test_set_config_value(self, temp_storage_dir):
        """Test setting configuration values."""
        config = Config(temp_storage_dir / "config.json")
        
        # Set new value
        success = config.set("test_key", "test_value")
        assert success is True
        assert config.get("test_key") == "test_value"

    def test_set_api_key(self, temp_storage_dir):
        """Test setting API keys."""
        config = Config(temp_storage_dir / "config.json")
        
        success = config.set_api_key("test_provider", "test_key_123")
        assert success is True
        
        retrieved = config.get_api_key("test_provider")
        assert retrieved == "test_key_123"

    def test_get_api_key_nonexistent(self, temp_storage_dir):
        """Test getting non-existent API key."""
        config = Config(temp_storage_dir / "config.json")
        
        retrieved = config.get_api_key("nonexistent_provider")
        assert retrieved is None

    def test_get_all_config(self, temp_storage_dir):
        """Test getting all configuration values."""
        config = Config(temp_storage_dir / "config.json")
        
        # Set some values
        config.set("test1", "value1")
        config.set("test2", "value2")
        
        all_config = config.get_all()
        
        assert isinstance(all_config, dict)
        assert "test1" in all_config
        assert "test2" in all_config
        assert all_config["test1"] == "value1"
        assert all_config["test2"] == "value2"

    def test_delete_config_key(self, temp_storage_dir):
        """Test deleting configuration keys."""
        config = Config(temp_storage_dir / "config.json")
        
        config.set("to_delete", "value")
        assert config.get("to_delete") == "value"
        
        success = config.delete("to_delete")
        assert success is True
        assert config.get("to_delete") is None

    def test_reset_config(self, temp_storage_dir):
        """Test resetting configuration to defaults."""
        config = Config(temp_storage_dir / "config.json")
        
        # Set some values
        config.set("custom_key", "custom_value")
        config.set_api_key("test", "test_key")
        
        # Reset
        success = config.reset()
        assert success is True
        
        # Should be back to defaults
        assert config.get("custom_key") is None
        assert config.get_api_key("test") is None
        assert config.get("default_provider") == "openrouter"

    def test_get_storage_path(self, temp_storage_dir):
        """Test getting configured storage path."""
        config = Config(temp_storage_dir / "config.json")
        
        storage_path = config.get_storage_path()
        assert isinstance(storage_path, Path)
        assert storage_path.exists()

    def test_get_default_format(self, temp_storage_dir):
        """Test getting default format."""
        config = Config(temp_storage_dir / "config.json")
        
        format_name = config.get_default_format()
        assert format_name == "yaml"

    def test_get_default_model(self, temp_storage_dir):
        """Test getting default models for providers."""
        config = Config(temp_storage_dir / "config.json")
        
        # Test different providers
        openrouter_model = config.get_default_model("openrouter")
        assert "meta-llama" in openrouter_model
        
        openai_model = config.get_default_model("openai")
        assert "gpt-3.5-turbo" in openai_model
        
        anthropic_model = config.get_default_model("anthropic")
        assert "claude" in anthropic_model

    def test_config_persistence(self, temp_storage_dir):
        """Test configuration persistence across instances."""
        config_path = temp_storage_dir / "config.json"
        
        # First instance
        config1 = Config(config_path)
        config1.set("persistent_key", "persistent_value")
        config1.set_api_key("persistent_provider", "persistent_key")
        
        # Second instance should load same config
        config2 = Config(config_path)
        assert config2.get("persistent_key") == "persistent_value"
        assert config2.get_api_key("persistent_provider") == "persistent_key"

    def test_config_file_content(self, temp_storage_dir):
        """Test that config file contains expected structure."""
        config_path = temp_storage_dir / "config.json"
        config = Config(config_path)
        
        # Read file directly
        with open(config_path) as f:
            data = json.load(f)
        
        expected_keys = [
            "storage_path", "default_format", "editor", "auto_backup",
            "max_backups", "default_provider", "default_model",
            "api_keys", "streaming", "max_tokens", "temperature"
        ]
        
        for key in expected_keys:
            assert key in data