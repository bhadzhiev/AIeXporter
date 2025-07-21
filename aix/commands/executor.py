import subprocess
import re
from typing import List, Tuple, Optional, Dict
from pathlib import Path
from .base import Command, SecurityValidator
from .security import DefaultSecurityValidator


class ShellCommand(Command):
    """A shell command that can be executed."""

    def __init__(
        self, command_string: str, working_dir: Optional[Path] = None, timeout: int = 30
    ):
        self.command_string = command_string
        self.working_dir = working_dir or Path.cwd()
        self.timeout = timeout

    def execute(self, *args, **kwargs) -> Tuple[bool, str, str]:
        """Execute the shell command."""
        try:
            result = subprocess.run(
                self.command_string,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.working_dir,
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {self.timeout} seconds"
        except Exception as e:
            return False, "", f"Error executing command: {str(e)}"

    def get_name(self) -> str:
        return self.command_string.split()[0] if self.command_string.strip() else ""

    def get_description(self) -> str:
        return f"Shell command: {self.command_string}"


class IntelligentShellCommand(ShellCommand):
    """Shell command with intelligent fallback alternatives."""

    def __init__(
        self, command_string: str, working_dir: Optional[Path] = None, timeout: int = 30
    ):
        super().__init__(command_string, working_dir, timeout)
        self.alternatives = self._build_alternatives()

    def execute(self, *args, **kwargs) -> Tuple[bool, str, str]:
        """Execute with intelligent fallbacks."""
        success, stdout, stderr = super().execute()
        if success:
            return success, stdout, stderr

        # Try alternatives
        for alt_command, reason in self.alternatives:
            alt_cmd = ShellCommand(alt_command, self.working_dir, self.timeout)
            success, stdout, stderr = alt_cmd.execute()
            if success:
                note = f"{stdout.strip()}\n[Note: Used '{alt_command}' instead of '{self.command_string}' ({reason})]"
                return True, note, stderr

        return False, stdout, stderr

    def _build_alternatives(self) -> List[Tuple[str, str]]:
        """Build intelligent alternatives for common commands."""
        cmd_parts = self.command_string.split()
        if not cmd_parts:
            return []

        base_cmd = cmd_parts[0]
        args = cmd_parts[1:] if len(cmd_parts) > 1 else []

        alternatives = []

        # Python alternatives
        if base_cmd == "python":
            alternatives.extend(
                [
                    (
                        "python3 " + " ".join(args),
                        "python3 commonly used instead of python",
                    ),
                    ("python3.12 " + " ".join(args), "trying specific Python version"),
                    ("/usr/bin/python3 " + " ".join(args), "using full path"),
                ]
            )

        # Git alternatives
        elif base_cmd == "git":
            if "not a git repository" in str(self):
                alternatives.extend(
                    [
                        (
                            "find . -name '.git' -type d 2>/dev/null | head -1",
                            "finding git repositories",
                        ),
                        ("ls -la", "showing directory contents"),
                    ]
                )

        # Node/npm alternatives
        elif base_cmd in ["node", "npm"]:
            alternatives.extend(
                [
                    ("which node || which nodejs", "checking for Node.js installation"),
                    (
                        "ls /usr/local/bin/node* 2>/dev/null || echo 'Node.js not found'",
                        "looking for Node.js binaries",
                    ),
                ]
            )

        # Docker alternatives
        elif base_cmd == "docker":
            alternatives.extend(
                [
                    (
                        "which docker || echo 'Docker not installed'",
                        "checking Docker installation",
                    ),
                    ("podman " + " ".join(args), "trying Podman as alternative"),
                ]
            )

        return alternatives


class CommandExecutor:
    """Orchestrator for command execution with security validation."""

    def __init__(
        self,
        security_validator: Optional[SecurityValidator] = None,
        working_dir: Optional[Path] = None,
        timeout: int = 30,
    ):
        self.security_validator = security_validator or DefaultSecurityValidator()
        self.working_dir = working_dir or Path.cwd()
        self.timeout = timeout

    def create_command(self, command_string: str, intelligent: bool = True) -> Command:
        """Factory method to create appropriate command instance."""
        if intelligent:
            return IntelligentShellCommand(
                command_string, self.working_dir, self.timeout
            )
        return ShellCommand(command_string, self.working_dir, self.timeout)

    def execute(
        self, command_string: str, intelligent: bool = True
    ) -> Tuple[bool, str, str]:
        """Execute a command with security validation."""
        if not self.security_validator.is_allowed(command_string):
            return False, "", self.security_validator.get_error_message(command_string)

        command = self.create_command(command_string, intelligent)
        return command.execute()

    def is_command_allowed(self, command_string: str) -> bool:
        """Check if command is allowed by security validator."""
        return self.security_validator.is_allowed(command_string)

    def process_template(
        self, template: str, variables: Dict[str, str]
    ) -> Tuple[str, Dict[str, str]]:
        """
        Process a template by substituting variables and executing commands.

        Args:
            template: The template string to process
            variables: Dictionary of variables to substitute

        Returns:
            Tuple of (processed_template, command_outputs)
        """
        result = template
        command_outputs = {}

        # First, substitute simple variables
        for var_name, var_value in variables.items():
            result = result.replace(f"{{{var_name}}}", var_value)

        # Process command patterns: $(command) and {cmd:command} and {exec:command}
        command_patterns = [
            (r"\$\(([^)]+)\)", "$(...)"),
            (r"\{cmd:([^}]+)\}", "{cmd:...}"),
            (r"\{exec:([^}]+)\}", "{exec:...}"),
        ]

        for pattern, placeholder_format in command_patterns:
            matches = re.findall(pattern, result)
            for cmd in matches:
                if cmd not in command_outputs:  # Avoid duplicate execution
                    success, stdout, stderr = self.execute(cmd)
                    command_output = stdout if success else stderr
                    command_outputs[cmd] = command_output.strip()

                # Replace the command placeholder with actual output
                if placeholder_format == "$(...)":
                    result = result.replace(f"$({cmd})", command_outputs[cmd])
                elif placeholder_format == "{cmd:...}":
                    result = result.replace(f"{{cmd:{cmd}}}", command_outputs[cmd])
                elif placeholder_format == "{exec:...}":
                    result = result.replace(f"{{exec:{cmd}}}", command_outputs[cmd])

        return result, command_outputs
