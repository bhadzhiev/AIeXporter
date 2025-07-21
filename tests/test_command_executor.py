from pathlib import Path
from aix.commands import CommandExecutor


class TestCommandExecutor:
    """Test command execution functionality without mocks."""

    def test_initialization_with_defaults(self):
        """Test executor initialization with default settings."""
        executor = CommandExecutor()

        # Default security validator should be used
        assert executor.security_validator is not None
        assert executor.working_dir == Path.cwd()

    def test_initialization_with_custom_settings(self, temp_dir):
        """Test executor initialization with custom settings."""
        from aix.commands import DefaultSecurityValidator

        custom_disabled = ["rm", "sudo", "dangerous-cmd"]
        security_validator = DefaultSecurityValidator(disabled_commands=custom_disabled)
        executor = CommandExecutor(
            security_validator=security_validator, working_dir=temp_dir
        )

        assert executor.working_dir == temp_dir
        assert executor.security_validator.disabled_commands == custom_disabled

    def test_is_command_allowed_allowed(self):
        """Test allowed command detection."""
        from aix.commands import DefaultSecurityValidator

        security_validator = DefaultSecurityValidator(disabled_commands=["rm", "sudo"])
        executor = CommandExecutor(security_validator=security_validator)

        assert executor.is_command_allowed("echo hello") is True
        assert executor.is_command_allowed("ls -la") is True
        assert executor.is_command_allowed("cat file.txt") is True
        assert executor.is_command_allowed("git status") is True

    def test_is_command_allowed_not_allowed(self):
        """Test disallowed command detection."""
        from aix.commands import DefaultSecurityValidator

        security_validator = DefaultSecurityValidator(
            disabled_commands=["rm", "sudo", "dangerous"]
        )
        executor = CommandExecutor(security_validator=security_validator)

        assert executor.is_command_allowed("rm -rf /") is False
        assert executor.is_command_allowed("sudo apt-get install") is False
        assert executor.is_command_allowed("dangerous command") is False
        assert executor.is_command_allowed("") is False

    def test_execute_allowed_command(self):
        """Test executing an allowed command."""
        from aix.commands import DefaultSecurityValidator

        security_validator = DefaultSecurityValidator(disabled_commands=["rm", "sudo"])
        executor = CommandExecutor(security_validator=security_validator)

        success, stdout, stderr = executor.execute("echo hello")

        assert success is True
        assert stdout.strip() == "hello"
        assert stderr == ""

    def test_execute_command_in_working_dir(self, temp_dir):
        """Test command execution in specific working directory."""
        from aix.commands import DefaultSecurityValidator

        security_validator = DefaultSecurityValidator(disabled_commands=["rm"])
        executor = CommandExecutor(
            security_validator=security_validator, working_dir=temp_dir
        )

        success, stdout, stderr = executor.execute("pwd")

        assert success is True
        assert str(temp_dir) in stdout.strip()

    def test_execute_disallowed_command(self):
        """Test executing a disallowed command."""
        from aix.commands import DefaultSecurityValidator

        security_validator = DefaultSecurityValidator(disabled_commands=["rm"])
        executor = CommandExecutor(security_validator=security_validator)

        success, stdout, stderr = executor.execute("rm nonexistent")

        assert success is False
        assert stdout == ""
        assert "Command disabled for security: rm nonexistent" in stderr

    def test_execute_command_timeout(self):
        """Test command timeout functionality."""
        from aix.commands import DefaultSecurityValidator

        security_validator = DefaultSecurityValidator(disabled_commands=["rm"])
        executor = CommandExecutor(security_validator=security_validator, timeout=1)

        # Sleep command should timeout
        success, stdout, stderr = executor.execute("sleep 2")

        assert success is False
        assert stdout == ""
        assert "timed out after 1 seconds" in stderr

    def test_invalid_command_syntax(self):
        """Test handling of invalid command syntax."""
        from aix.commands import DefaultSecurityValidator

        security_validator = DefaultSecurityValidator()
        executor = CommandExecutor(security_validator=security_validator)

        # Malformed command - should be handled gracefully
        success, stdout, stderr = executor.execute("invalid command with bad syntax")

        # Should handle gracefully and return error
        assert success is False

    def test_command_with_spaces(self):
        """Test commands with spaces and arguments."""
        from aix.commands import DefaultSecurityValidator

        security_validator = DefaultSecurityValidator(disabled_commands=["rm"])
        executor = CommandExecutor(security_validator=security_validator)

        success, stdout, stderr = executor.execute("echo 'hello world'")

        assert success is True
        assert "hello world" in stdout

    def test_empty_command(self):
        """Test handling of empty commands."""
        from aix.commands import DefaultSecurityValidator

        security_validator = DefaultSecurityValidator()
        executor = CommandExecutor(security_validator=security_validator)

        success, stdout, stderr = executor.execute("")

        assert success is False
        assert "Command disabled for security" in stderr
