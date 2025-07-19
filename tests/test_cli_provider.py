import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner

from aix.cli import app


class TestProviderCLI:
    """Test provider CLI commands."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.json"

        # Set environment variable to use temp directory
        os.environ["AIX_STORAGE_PATH"] = self.temp_dir

    def teardown_method(self):
        """Clean up test environment."""
        # Clean up environment variable
        if "AIX_STORAGE_PATH" in os.environ:
            del os.environ["AIX_STORAGE_PATH"]

    def test_provider_list_empty(self):
        """Test listing providers when none exist."""
        result = self.runner.invoke(app, ["provider", "list"])

        assert result.exit_code == 0
        assert "No custom providers configured" in result.stdout
        assert "aix provider add" in result.stdout

    def test_provider_add_basic(self):
        """Test adding a basic custom provider."""
        result = self.runner.invoke(
            app, ["provider", "add", "test-provider", "http://localhost:8080/v1"]
        )

        assert result.exit_code == 0
        assert "Custom provider 'test-provider' added successfully!" in result.stdout
        assert "aix run <prompt> --provider custom:test-provider" in result.stdout

    def test_provider_add_with_options(self):
        """Test adding a custom provider with all options."""
        result = self.runner.invoke(
            app,
            [
                "provider",
                "add",
                "full-provider",
                "http://localhost:11434/v1",
                "--model",
                "llama3.2",
                "--header",
                "X-Custom-Auth:bearer-token",
                "--header",
                "X-API-Version:1.0",
                "--auth-type",
                "api-key",
            ],
        )

        assert result.exit_code == 0
        assert "Custom provider 'full-provider' added successfully!" in result.stdout

    def test_provider_add_invalid_header(self):
        """Test adding provider with invalid header format."""
        result = self.runner.invoke(
            app,
            [
                "provider",
                "add",
                "bad-provider",
                "http://localhost:8080/v1",
                "--header",
                "invalid-header-format",
            ],
        )

        assert result.exit_code == 0
        assert "Invalid header format" in result.stdout
        assert "Use key:value format" in result.stdout

    def test_provider_list_with_providers(self):
        """Test listing providers when some exist."""
        # Add a provider first
        self.runner.invoke(
            app,
            [
                "provider",
                "add",
                "test-provider",
                "http://localhost:8080/v1",
                "--model",
                "test-model",
            ],
        )

        result = self.runner.invoke(app, ["provider", "list"])

        assert result.exit_code == 0
        assert "Custom Providers" in result.stdout
        assert "test-provider" in result.stdout
        assert "http://localhost:8080/v1" in result.stdout
        assert "test-model" in result.stdout
        assert "bearer" in result.stdout

    def test_provider_info_existing(self):
        """Test getting info for an existing provider."""
        # Add a provider first
        self.runner.invoke(
            app,
            [
                "provider",
                "add",
                "info-provider",
                "http://test.com/v1",
                "--model",
                "info-model",
                "--header",
                "X-Test:test-value",
            ],
        )

        result = self.runner.invoke(app, ["provider", "info", "info-provider"])

        assert result.exit_code == 0
        assert "Custom Provider: info-provider" in result.stdout
        assert "Base URL: http://test.com/v1" in result.stdout
        assert "Default Model: info-model" in result.stdout
        assert "Auth Type: bearer" in result.stdout
        assert "Custom Headers:" in result.stdout
        assert "X-Test: test-value" in result.stdout

    def test_provider_info_nonexistent(self):
        """Test getting info for a non-existent provider."""
        result = self.runner.invoke(app, ["provider", "info", "nonexistent"])

        assert result.exit_code == 0
        assert "Custom provider 'nonexistent' not found" in result.stdout

    def test_provider_remove_existing(self):
        """Test removing an existing provider."""
        # Add a provider first
        self.runner.invoke(
            app, ["provider", "add", "remove-me", "http://remove.com/v1"]
        )

        result = self.runner.invoke(app, ["provider", "remove", "remove-me"])

        assert result.exit_code == 0
        assert "Custom provider 'remove-me' removed successfully!" in result.stdout

    def test_provider_remove_nonexistent(self):
        """Test removing a non-existent provider."""
        result = self.runner.invoke(app, ["provider", "remove", "nonexistent"])

        assert result.exit_code == 0
        assert "Custom provider 'nonexistent' not found" in result.stdout

    def test_provider_workflow(self):
        """Test complete provider management workflow."""
        # Add provider
        result = self.runner.invoke(
            app,
            [
                "provider",
                "add",
                "workflow-test",
                "http://workflow.com/v1",
                "--model",
                "workflow-model",
                "--header",
                "X-Workflow:test",
            ],
        )
        assert result.exit_code == 0
        assert "added successfully" in result.stdout

        # List providers
        result = self.runner.invoke(app, ["provider", "list"])
        assert result.exit_code == 0
        assert "workflow-test" in result.stdout

        # Get info
        result = self.runner.invoke(app, ["provider", "info", "workflow-test"])
        assert result.exit_code == 0
        assert "workflow-model" in result.stdout
        assert "X-Workflow: test" in result.stdout

        # Remove provider
        result = self.runner.invoke(app, ["provider", "remove", "workflow-test"])
        assert result.exit_code == 0
        assert "removed successfully" in result.stdout

        # Verify removal
        result = self.runner.invoke(app, ["provider", "list"])
        assert result.exit_code == 0
        assert "No custom providers configured" in result.stdout

    def test_provider_help_commands(self):
        """Test help for provider commands."""
        # Main provider help
        result = self.runner.invoke(app, ["provider", "--help"])
        assert result.exit_code == 0
        assert "Manage custom API providers" in result.stdout
        assert "add" in result.stdout
        assert "list" in result.stdout
        assert "remove" in result.stdout
        assert "info" in result.stdout

        # Add command help
        result = self.runner.invoke(app, ["provider", "add", "--help"])
        assert result.exit_code == 0
        assert "Add a custom API provider" in result.stdout
        assert "base_url" in result.stdout
        assert "--model" in result.stdout
        assert "--header" in result.stdout
        assert "--auth-type" in result.stdout

    def test_provider_config_persistence(self):
        """Test that provider config persists across CLI invocations."""
        # Add provider in first invocation
        result1 = self.runner.invoke(
            app, ["provider", "add", "persistent", "http://persist.com/v1"]
        )
        assert result1.exit_code == 0

        # List providers in second invocation
        result2 = self.runner.invoke(app, ["provider", "list"])
        assert result2.exit_code == 0
        assert "persistent" in result2.stdout
        assert "http://persist.com/v1" in result2.stdout

    def test_custom_provider_validation(self):
        """Test that custom provider validation works."""
        # Add a custom provider first
        self.runner.invoke(
            app, ["provider", "add", "test-provider", "http://localhost:8080/v1"]
        )

        # Test provider completion includes custom providers
        from aix.completion import complete_providers

        providers = complete_providers("")
        custom_providers = [p for p in providers if p.startswith("custom:")]
        assert len(custom_providers) > 0
        assert "custom:test-provider" in providers
