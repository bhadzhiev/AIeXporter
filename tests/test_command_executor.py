from pathlib import Path
from aix.command_executor import CommandExecutor


class TestCommandExecutor:
    """Test command execution functionality without mocks."""

    def test_initialization_with_defaults(self):
        """Test executor initialization with default settings."""
        executor = CommandExecutor()

        # Default disabled commands should be populated
        assert len(executor.disabled_commands) > 0
        assert "rm" in executor.disabled_commands
        assert "sudo" in executor.disabled_commands
        assert executor.working_dir == Path.cwd()

    def test_initialization_with_custom_settings(self, temp_dir):
        """Test executor initialization with custom settings."""
        custom_disabled = ["rm", "sudo", "dangerous-cmd"]
        executor = CommandExecutor(
            disabled_commands=custom_disabled, working_dir=temp_dir
        )

        assert executor.disabled_commands == custom_disabled
        assert executor.working_dir == temp_dir

    def test_is_command_allowed_allowed(self):
        """Test allowed command detection."""
        executor = CommandExecutor(disabled_commands=["rm", "sudo"])

        assert executor.is_command_allowed("echo hello") is True
        assert executor.is_command_allowed("ls -la") is True
        assert executor.is_command_allowed("cat file.txt") is True
        assert executor.is_command_allowed("git status") is True

    def test_is_command_allowed_not_allowed(self):
        """Test disallowed command detection."""
        executor = CommandExecutor(disabled_commands=["rm", "sudo", "dangerous"])

        assert executor.is_command_allowed("rm -rf /") is False
        assert executor.is_command_allowed("sudo apt-get install") is False
        assert executor.is_command_allowed("dangerous command") is False
        assert executor.is_command_allowed("") is False

    def test_execute_allowed_command(self):
        """Test executing an allowed command."""
        executor = CommandExecutor(disabled_commands=["rm", "sudo"])  # echo not disabled

        success, stdout, stderr = executor.execute_command("echo hello")

        assert success is True
        assert stdout.strip() == "hello"
        assert stderr == ""

    def test_execute_command_in_working_dir(self, temp_dir):
        """Test command execution in specific working directory."""
        executor = CommandExecutor(disabled_commands=["rm"], working_dir=temp_dir)  # pwd not disabled

        success, stdout, stderr = executor.execute_command("pwd")

        assert success is True
        assert str(temp_dir) in stdout.strip()

    def test_execute_disallowed_command(self):
        """Test executing a disallowed command."""
        executor = CommandExecutor(disabled_commands=["rm"])

        success, stdout, stderr = executor.execute_command("rm nonexistent")

        assert success is False
        assert stdout == ""
        assert "Command disabled for security: rm nonexistent" in stderr

    def test_execute_command_timeout(self):
        """Test command timeout functionality."""
        executor = CommandExecutor(disabled_commands=["rm"])  # sleep not disabled

        # Sleep command should timeout
        success, stdout, stderr = executor.execute_command("sleep 2", timeout=1)

        assert success is False
        assert stdout == ""
        assert "timed out after 1 seconds" in stderr

    def test_extract_shell_commands(self):
        """Test extraction of $(command) syntax."""
        executor = CommandExecutor()

        text = "Hello $(whoami), your path is $(pwd)"
        commands = executor.extract_commands(text)

        assert len(commands) == 2
        assert commands[0][0] == "$(whoami)"
        assert commands[0][1] == "whoami"
        assert commands[1][0] == "$(pwd)"
        assert commands[1][1] == "pwd"

    def test_extract_cmd_commands(self):
        """Test extraction of {cmd:command} syntax."""
        executor = CommandExecutor()

        text = "User: {cmd:whoami}, Date: {cmd:date}"
        commands = executor.extract_commands(text)

        assert len(commands) == 2
        assert commands[0][0] == "{cmd:whoami}"
        assert commands[0][1] == "whoami"
        assert commands[1][0] == "{cmd:date}"
        assert commands[1][1] == "date"

    def test_extract_exec_commands(self):
        """Test extraction of {exec:command} syntax."""
        executor = CommandExecutor()

        text = "Path: {exec:pwd}, Time: {exec:date}"
        commands = executor.extract_commands(text)

        assert len(commands) == 2
        assert commands[0][0] == "{exec:pwd}"
        assert commands[0][1] == "pwd"
        assert commands[1][0] == "{exec:date}"
        assert commands[1][1] == "date"

    def test_extract_mixed_commands(self):
        """Test extraction of mixed command syntaxes."""
        executor = CommandExecutor()

        text = "User: $(whoami), Path: {cmd:pwd}, Time: {exec:date}"
        commands = executor.extract_commands(text)

        assert len(commands) == 3
        assert any(cmd[0] == "$(whoami)" for cmd in commands)
        assert any(cmd[0] == "{cmd:pwd}" for cmd in commands)
        assert any(cmd[0] == "{exec:date}" for cmd in commands)

    def test_process_template_with_commands(self):
        """Test processing template with commands."""
        executor = CommandExecutor(disabled_commands=["rm"])  # whoami, echo not disabled

        template = "Hello $(echo world), user: $(whoami)"
        result, command_outputs = executor.process_template(template)

        assert "world" in result
        assert "$(whoami)" in command_outputs
        assert "$(echo world)" in command_outputs

    def test_process_template_with_variables(self):
        """Test processing template with variables."""
        executor = CommandExecutor()

        template = "Hello {name}, your path is {path}"
        variables = {"name": "Alice", "path": "/home/alice"}

        result, _ = executor.process_template(template, variables)

        assert result == "Hello Alice, your path is /home/alice"

    def test_process_template_with_variables_and_commands(self):
        """Test processing template with both variables and commands."""
        executor = CommandExecutor(disabled_commands=["rm"])  # whoami not disabled

        template = "Hello {name}, user: $(whoami)"
        variables = {"name": "Alice"}

        result, command_outputs = executor.process_template(template, variables)

        assert "Alice" in result
        assert "$(whoami)" in command_outputs

    def test_get_command_info_allowed(self):
        """Test getting info for allowed commands."""
        executor = CommandExecutor(disabled_commands=["rm"])  # echo not disabled

        info = executor.get_command_info("echo")

        assert isinstance(info, dict)
        # echo should have help text
        assert "help" in info or "version" in info

    def test_get_command_info_disallowed(self):
        """Test getting info for disallowed commands."""
        executor = CommandExecutor(disabled_commands=["rm"])

        info = executor.get_command_info("rm")

        assert "error" in info
        assert "Command disabled for security" in info["error"]

    def test_invalid_command_syntax(self):
        """Test handling of invalid command syntax."""
        executor = CommandExecutor()

        # Malformed command
        success, stdout, stderr = executor.execute_command(
            "invalid command with bad syntax"
        )

        # Should handle gracefully and return error
        assert success is False

    def test_command_with_spaces(self):
        """Test commands with spaces and arguments."""
        executor = CommandExecutor(disabled_commands=["rm"])  # echo not disabled

        success, stdout, stderr = executor.execute_command("echo 'hello world'")

        assert success is True
        assert "hello world" in stdout

    def test_empty_command(self):
        """Test handling of empty commands."""
        executor = CommandExecutor()

        success, stdout, stderr = executor.execute_command("")

        assert success is False
        assert "Command disabled for security" in stderr
