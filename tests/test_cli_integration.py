import pytest
import tempfile
import shutil
import subprocess
import json
import yaml
import os
from pathlib import Path


class TestCLIIntegration:
    """Integration tests for CLI commands without mocks."""

    @pytest.fixture
    def temp_env(self):
        """Create temporary environment for CLI testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Set custom prompts directory
            env = {
                **dict(os.environ),
                "AIX_STORAGE_PATH": str(tmp_path / ".prompts")
            }
            
            yield {
                "temp_dir": tmp_path,
                "env": env,
                "prompts_dir": tmp_path / ".prompts"
            }

    def run_cli_command(self, cmd_args, temp_env):
        """Run CLI command and return result."""
        cmd = ["python", "-m", "aix.cli"] + cmd_args
        
        try:
            result = subprocess.run(
                cmd,
                env=temp_env["env"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(cmd, 1, "", "Command timed out")

    def test_create_prompt_cli(self, temp_env):
        """Test creating a prompt via CLI."""
        result = self.run_cli_command([
            "create", "test-prompt",
            "Hello {name}, welcome to {place}!",
            "--desc", "A test prompt",
            "--tag", "test"
        ], temp_env)
        
        assert result.returncode == 0
        assert "test-prompt created successfully" in result.stdout
        
        # Verify files created
        yaml_file = temp_env["prompts_dir"] / "test-prompt.yaml"
        txt_file = temp_env["prompts_dir"] / "test-prompt.txt"
        assert yaml_file.exists()
        assert txt_file.exists()

    def test_list_prompts_cli(self, temp_env):
        """Test listing prompts via CLI."""
        # Create a prompt first
        self.run_cli_command([
            "create", "list-test",
            "Test template",
            "--desc", "For listing test"
        ], temp_env)
        
        # List prompts
        result = self.run_cli_command(["list"], temp_env)
        
        assert result.returncode == 0
        assert "list-test" in result.stdout

    def test_show_prompt_cli(self, temp_env):
        """Test showing prompt details via CLI."""
        self.run_cli_command([
            "create", "show-test",
            "Hello {name}!",
            "--desc", "Show test prompt"
        ], temp_env)
        
        result = self.run_cli_command(["show", "show-test"], temp_env)
        
        assert result.returncode == 0
        assert "Show test prompt" in result.stdout
        assert "Hello {name}!" in result.stdout

    def test_delete_prompt_cli(self, temp_env):
        """Test deleting a prompt via CLI."""
        self.run_cli_command([
            "create", "delete-test",
            "Template to delete"
        ], temp_env)
        
        # Verify it exists
        yaml_file = temp_env["prompts_dir"] / "delete-test.yaml"
        assert yaml_file.exists()
        
        # Delete with force flag
        result = self.run_cli_command(["delete", "delete-test", "--force"], temp_env)
        
        assert result.returncode == 0
        assert "deleted successfully" in result.stdout
        assert not yaml_file.exists()

    def test_create_collection_cli(self, temp_env):
        """Test creating collections via CLI."""
        result = self.run_cli_command([
            "collection-create", "test-collection",
            "--description", "Test collection",
            "--template", "prompt1",
            "--template", "prompt2"
        ], temp_env)
        
        assert result.returncode == 0
        
        # Verify collection file exists
        collection_file = temp_env["prompts_dir"] / "collections" / "test-collection.yaml"
        assert collection_file.exists()

    def test_config_cli(self, temp_env):
        """Test configuration management via CLI."""
        # Set a value
        result = self.run_cli_command([
            "config", "--set", "test_key=test_value"
        ], temp_env)
        
        assert result.returncode == 0
        
        # Get the value
        result = self.run_cli_command([
            "config", "--get", "test_key"
        ], temp_env)
        
        assert result.returncode == 0
        assert "test_value" in result.stdout

    def test_dry_run_command(self, temp_env):
        """Test dry run functionality."""
        # Create a prompt
        self.run_cli_command([
            "create", "dry-test",
            "Hello {name}, your favorite color is {color}!"
        ], temp_env)
        
        # Test dry run
        result = self.run_cli_command([
            "run", "dry-test",
            "--param", "name=Alice",
            "--param", "color=blue",
            "--dry-run"
        ], temp_env)
        
        assert result.returncode == 0
        assert "Alice" in result.stdout
        assert "blue" in result.stdout
        assert "Hello Alice, your favorite color is blue!" in result.stdout

    def test_collection_list_cli(self, temp_env):
        """Test listing collections via CLI."""
        # Create collection
        self.run_cli_command([
            "collection-create", "list-test-collection",
            "--description", "For listing"
        ], temp_env)
        
        # List collections
        result = self.run_cli_command(["collection-list"], temp_env)
        
        assert result.returncode == 0
        assert "list-test-collection" in result.stdout

    def test_template_with_commands_dry_run(self, temp_env):
        """Test template with commands in dry run mode."""
        self.run_cli_command([
            "create", "command-test",
            "User: $(whoami), Path: $(pwd), Name: {name}"
        ], temp_env)
        
        result = self.run_cli_command([
            "run", "command-test",
            "--param", "name=TestUser",
            "--dry-run"
        ], temp_env)
        
        assert result.returncode == 0
        assert "TestUser" in result.stdout

    def test_yaml_and_json_formats(self, temp_env):
        """Test creating prompts in both YAML and JSON formats."""
        # Test YAML
        result = self.run_cli_command([
            "create", "yaml-test",
            "YAML template",
            "--format", "yaml"
        ], temp_env)
        
        assert result.returncode == 0
        assert (temp_env["prompts_dir"] / "yaml-test.yaml").exists()
        
        # Test JSON
        result = self.run_cli_command([
            "create", "json-test",
            "JSON template",
            "--format", "json"
        ], temp_env)
        
        assert result.returncode == 0
        assert (temp_env["prompts_dir"] / "json-test.json").exists()

    def test_help_commands(self, temp_env):
        """Test help commands work correctly."""
        result = self.run_cli_command(["--help"], temp_env)
        assert result.returncode == 0
        assert "Commands:" in result.stdout
        
        result = self.run_cli_command(["create", "--help"], temp_env)
        assert result.returncode == 0
        assert "Create a new prompt template" in result.stdout

    def test_error_handling(self, temp_env):
        """Test error handling for invalid commands."""
        # Try to run non-existent prompt
        result = self.run_cli_command(["run", "nonexistent"], temp_env)
        
        assert result.returncode != 0
        assert "nonexistent" in result.stdout

    def test_collection_workflow(self, temp_env):
        """Test complete collection workflow."""
        # Create prompts
        self.run_cli_command([
            "create", "prompt1", "Template 1"
        ], temp_env)
        
        self.run_cli_command([
            "create", "prompt2", "Template 2"
        ], temp_env)
        
        # Create collection
        self.run_cli_command([
            "collection-create", "workflow-collection",
            "--description", "Workflow test",
            "--template", "prompt1",
            "--template", "prompt2"
        ], temp_env)
        
        # Load collection
        result = self.run_cli_command([
            "collection-load", "workflow-collection"
        ], temp_env)
        
        assert result.returncode == 0
        
        # List should show only collection templates
        result = self.run_cli_command(["list"], temp_env)
        
        assert result.returncode == 0
        assert "prompt1" in result.stdout
        assert "prompt2" in result.stdout
        
        # Unload collection
        result = self.run_cli_command(["collection-unload"], temp_env)
        assert result.returncode == 0

    def test_version_command(self, temp_env):
        """Test version command."""
        result = self.run_cli_command(["--version"], temp_env)
        
        assert result.returncode == 0
        assert "aix" in result.stdout
        assert "version" in result.stdout.lower()

    def test_complex_template_with_parameters(self, temp_env):
        """Test complex template with multiple parameters."""
        self.run_cli_command([
            "create", "complex-template",
            "Generate a {type} script for {language} that {description}. Include error handling for {error_type} errors."
        ], temp_env)
        
        result = self.run_cli_command([
            "run", "complex-template",
            "--param", "type=deployment",
            "--param", "language=python",
            "--param", "description=deploys to AWS",
            "--param", "error_type=network",
            "--dry-run"
        ], temp_env)
        
        assert result.returncode == 0
        assert "deployment" in result.stdout
        assert "python" in result.stdout
        assert "AWS" in result.stdout
        assert "network" in result.stdout