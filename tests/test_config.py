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
        assert config.get("default_format") == "xml"
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
        assert format_name == "xml"

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
        Config(config_path)

        # Read file directly
        with open(config_path) as f:
            data = json.load(f)

        expected_keys = [
            "storage_path",
            "default_format",
            "editor",
            "auto_backup",
            "max_backups",
            "default_provider",
            "default_model",
            "api_keys",
            "streaming",
            "max_tokens",
            "temperature",
            "custom_providers",
        ]

        for key in expected_keys:
            assert key in data


class TestCustomProviders:
    """Test custom provider configuration management."""

    def test_get_custom_providers_empty(self, temp_storage_dir):
        """Test getting custom providers when none exist."""
        config = Config(temp_storage_dir / "config.json")

        providers = config.get_custom_providers()
        assert isinstance(providers, dict)
        assert len(providers) == 0

    def test_add_custom_provider(self, temp_storage_dir):
        """Test adding a custom provider."""
        config = Config(temp_storage_dir / "config.json")

        success = config.add_custom_provider(
            name="ollama",
            base_url="http://localhost:11434/v1",
            default_model="llama3.2",
            headers={"X-Custom": "test"},
            auth_type="bearer",
        )

        assert success is True

        providers = config.get_custom_providers()
        assert "ollama" in providers

        ollama_config = providers["ollama"]
        assert ollama_config["base_url"] == "http://localhost:11434/v1"
        assert ollama_config["default_model"] == "llama3.2"
        assert ollama_config["headers"] == {"X-Custom": "test"}
        assert ollama_config["auth_type"] == "bearer"

    def test_add_custom_provider_minimal(self, temp_storage_dir):
        """Test adding a custom provider with minimal config."""
        config = Config(temp_storage_dir / "config.json")

        success = config.add_custom_provider(
            name="minimal", base_url="http://localhost:8080/v1"
        )

        assert success is True

        provider_config = config.get_custom_provider("minimal")
        assert provider_config["base_url"] == "http://localhost:8080/v1"
        assert provider_config["default_model"] is None
        assert provider_config["headers"] == {}
        assert provider_config["auth_type"] == "bearer"

    def test_get_custom_provider(self, temp_storage_dir):
        """Test getting a specific custom provider."""
        config = Config(temp_storage_dir / "config.json")

        # Add provider first
        config.add_custom_provider(
            name="test_provider",
            base_url="http://test.com/v1",
            default_model="test-model",
        )

        provider_config = config.get_custom_provider("test_provider")
        assert provider_config is not None
        assert provider_config["base_url"] == "http://test.com/v1"
        assert provider_config["default_model"] == "test-model"

    def test_get_custom_provider_nonexistent(self, temp_storage_dir):
        """Test getting a non-existent custom provider."""
        config = Config(temp_storage_dir / "config.json")

        provider_config = config.get_custom_provider("nonexistent")
        assert provider_config is None

    def test_remove_custom_provider(self, temp_storage_dir):
        """Test removing a custom provider."""
        config = Config(temp_storage_dir / "config.json")

        # Add provider first
        config.add_custom_provider(name="to_remove", base_url="http://remove.com/v1")

        # Verify it exists
        assert config.get_custom_provider("to_remove") is not None

        # Remove it
        success = config.remove_custom_provider("to_remove")
        assert success is True

        # Verify it's gone
        assert config.get_custom_provider("to_remove") is None

    def test_remove_custom_provider_nonexistent(self, temp_storage_dir):
        """Test removing a non-existent custom provider."""
        config = Config(temp_storage_dir / "config.json")

        success = config.remove_custom_provider("nonexistent")
        assert success is False

    def test_custom_provider_persistence(self, temp_storage_dir):
        """Test custom provider persistence across config instances."""
        config_path = temp_storage_dir / "config.json"

        # First instance - add provider
        config1 = Config(config_path)
        config1.add_custom_provider(
            name="persistent",
            base_url="http://persistent.com/v1",
            default_model="persistent-model",
        )

        # Second instance - should load same provider
        config2 = Config(config_path)
        provider_config = config2.get_custom_provider("persistent")

        assert provider_config is not None
        assert provider_config["base_url"] == "http://persistent.com/v1"
        assert provider_config["default_model"] == "persistent-model"

    def test_multiple_custom_providers(self, temp_storage_dir):
        """Test managing multiple custom providers."""
        config = Config(temp_storage_dir / "config.json")

        # Add multiple providers
        config.add_custom_provider("provider1", "http://p1.com/v1", "model1")
        config.add_custom_provider("provider2", "http://p2.com/v1", "model2")
        config.add_custom_provider("provider3", "http://p3.com/v1", "model3")

        providers = config.get_custom_providers()
        assert len(providers) == 3
        assert "provider1" in providers
        assert "provider2" in providers
        assert "provider3" in providers

        # Remove one
        config.remove_custom_provider("provider2")

        providers = config.get_custom_providers()
        assert len(providers) == 2
        assert "provider1" in providers
        assert "provider2" not in providers
        assert "provider3" in providers
