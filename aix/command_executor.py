import subprocess
import shlex
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class CommandExecutor:
    """Execute shell commands safely and capture their output for use in prompts."""

    def __init__(
        self,
        disabled_commands: Optional[List[str]] = None,
        working_dir: Optional[Path] = None,
    ):
        """
        Initialize command executor with security constraints.

        Args:
            disabled_commands: List of disabled command prefixes. If None, uses default dangerous commands list.
            working_dir: Working directory for command execution. Defaults to current directory.
        """
        self.disabled_commands = disabled_commands or [
            "rm",
            "rmdir",
            "del",
            "delete",
            "format",
            "fdisk",
            "mkfs",
            "dd",
            "shutdown",
            "reboot",
            "halt",
            "poweroff",
            "init",
            "kill",
            "killall",
            "pkill",
            "chmod",
            "chown",
            "chgrp",
            "passwd",
            "sudo",
            "su",
            "doas",
            "runas",
            "mv",  # Can be dangerous when moving system files
            "cp /",  # Dangerous when copying to root
            "rsync /",  # Dangerous when syncing to root
            "tar --",  # Dangerous tar operations
            "gzip -d /",  # Dangerous decompression
            "gunzip /",
            "unzip /",
            "wget",  # Network access
            "curl",  # Network access
            "ssh",  # Network access
            "scp",  # Network access
            "ftp",  # Network access
            "sftp",  # Network access
            "nc",  # Network access
            "netcat",  # Network access
            "telnet",  # Network access
            "ping -f",  # Flood ping
            "fork",  # Fork bomb potential
            ":()",  # Fork bomb
            "eval",  # Code injection
            "exec",  # Code execution
            "source",  # Script execution
            ".",  # Script execution (dot command)
        ]
        self.working_dir = working_dir or Path.cwd()

    def is_command_allowed(self, command: str) -> bool:
        """Check if a command is allowed to be executed (not in disabled list)."""
        if not command.strip():
            return False

        # Parse the command to get the base command
        try:
            parsed = shlex.split(command)
            if not parsed:
                return False
            base_command = parsed[0]
            
            # Check the full command line against disabled patterns
            command_lower = command.lower().strip()
            
            # Check against disabled commands
            for disabled in self.disabled_commands:
                if base_command.startswith(disabled) or disabled in command_lower:
                    return False
                    
            # Additional security checks
            if self._contains_dangerous_patterns(command):
                return False
                
            return True
        except ValueError:
            # Invalid shell syntax
            return False
            
    def _contains_dangerous_patterns(self, command: str) -> bool:
        """Check for dangerous command patterns."""
        dangerous_patterns = [
            r"rm\s+-rf\s+/",  # rm -rf /
            r":\(\)\s*\{\s*:\|:\&\s*\}\s*;\s*:",  # fork bomb
            r"\>\s*/dev/sd[a-z]",  # writing to disk devices
            r"dd\s+.*of\s*=\s*/dev/",  # dd to devices
            r"chmod\s+777\s+/",  # chmod 777 /
            r"chown\s+.*\s+/",  # chown root files
            r"\|\s*sh",  # piping to shell
            r"\$\(.*\$\(.*\).*\)",  # nested command substitution (potential injection)
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True
                
        return False

    def execute_command(self, command: str, timeout: int = 30) -> Tuple[bool, str, str]:
        """
        Execute a shell command and return success status, stdout, and stderr.

        Args:
            command: Shell command to execute
            timeout: Timeout in seconds

        Returns:
            Tuple of (success: bool, stdout: str, stderr: str)
        """
        if not self.is_command_allowed(command):
            return False, "", f"Command disabled for security: {command}"

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.working_dir,
            )

            return result.returncode == 0, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", f"Error executing command: {str(e)}"

    def try_command_alternatives(self, command: str) -> Tuple[bool, str, str]:
        """
        Try command alternatives and intelligent fallbacks for common failures.

        Args:
            command: Original command that failed

        Returns:
            Tuple of (success: bool, stdout: str, stderr: str)
        """
        # Try the original command first
        success, stdout, stderr = self.execute_command(command)
        if success:
            return success, stdout, stderr

        # Common command alternatives
        alternatives = self._get_command_alternatives(command, stderr)

        for alt_command, reason in alternatives:
            success, stdout, stderr = self.execute_command(alt_command)
            if success:
                # Add note about which alternative worked
                note = f"{stdout.strip()}\n[Note: Used '{alt_command}' instead of '{command}' ({reason})]"
                return True, note, stderr

        # No alternatives worked, return original error
        return False, stdout, stderr

    def _get_command_alternatives(
        self, command: str, error: str
    ) -> List[Tuple[str, str]]:
        """
        Get intelligent alternatives for failed commands.

        Args:
            command: The failed command
            error: The error message

        Returns:
            List of (alternative_command, reason) tuples
        """
        alternatives = []
        cmd_parts = command.split()
        if not cmd_parts:
            return alternatives

        base_cmd = cmd_parts[0]
        args = cmd_parts[1:] if len(cmd_parts) > 1 else []

        # Python alternatives
        if base_cmd == "python":
            if "command not found" in error.lower() or "not found" in error.lower():
                alternatives.extend(
                    [
                        (
                            "python3 " + " ".join(args),
                            "python3 commonly used instead of python",
                        ),
                        (
                            "python3.12 " + " ".join(args),
                            "trying specific Python version",
                        ),
                        (
                            "python3.11 " + " ".join(args),
                            "trying specific Python version",
                        ),
                        ("/usr/bin/python3 " + " ".join(args), "using full path"),
                    ]
                )

        # Git alternatives and context-aware suggestions
        if base_cmd == "git":
            if "not a git repository" in error.lower():
                # Try to find git repos in common locations
                alternatives.extend(
                    [
                        (
                            "find . -name '.git' -type d 2>/dev/null | head -1",
                            "finding git repositories",
                        ),
                        (
                            "ls -la",
                            "showing directory contents to understand structure",
                        ),
                    ]
                )
            elif "unknown revision" in error.lower():
                alternatives.extend(
                    [
                        ("git status", "checking repository status"),
                        ("git branch -a", "listing all branches"),
                    ]
                )

        # Node/npm alternatives
        if base_cmd in ["node", "npm"]:
            if "command not found" in error.lower():
                alternatives.extend(
                    [
                        (
                            "which node || which nodejs",
                            "checking for Node.js installation",
                        ),
                        (
                            "ls /usr/local/bin/node* 2>/dev/null || echo 'Node.js not found'",
                            "looking for Node.js binaries",
                        ),
                    ]
                )

        # Docker alternatives
        if base_cmd == "docker":
            if "command not found" in error.lower():
                alternatives.extend(
                    [
                        (
                            "which docker || echo 'Docker not installed'",
                            "checking Docker installation",
                        ),
                        ("podman " + " ".join(args), "trying Podman as alternative"),
                    ]
                )

        # General "command not found" handling
        if "command not found" in error.lower() or "not found" in error.lower():
            alternatives.extend(
                [
                    (
                        f"which {base_cmd} || echo 'Command {base_cmd} not found in PATH'",
                        "checking if command exists",
                    ),
                    (f"whereis {base_cmd}", "finding command location"),
                    ("echo $PATH", "showing current PATH"),
                ]
            )

        # Permission denied handling
        if "permission denied" in error.lower():
            alternatives.extend(
                [
                    (
                        f"ls -la $(which {base_cmd} 2>/dev/null || echo '/usr/bin/{base_cmd}')",
                        "checking command permissions",
                    ),
                ]
            )

        return alternatives

    def _format_intelligent_error(self, command: str, error: str) -> str:
        """
        Format an intelligent error message with helpful suggestions.

        Args:
            command: The failed command
            error: The error message

        Returns:
            Formatted error message with suggestions
        """
        base_cmd = command.split()[0] if command.split() else ""
        error_clean = error.strip()

        # Specific error suggestions
        suggestions = []

        if "not a git repository" in error.lower():
            suggestions.extend(
                [
                    "Run this command from within a git repository",
                    "Initialize git with: git init",
                    "Check current directory with: pwd",
                ]
            )

        elif "command not found" in error.lower() and base_cmd == "python":
            suggestions.extend(
                [
                    "Try using 'python3' instead of 'python'",
                    "Install Python: brew install python (macOS) or apt-get install python3 (Linux)",
                    "Check Python installation with: which python3",
                ]
            )

        elif "command not found" in error.lower():
            suggestions.extend(
                [
                    f"Install {base_cmd} or check if it's in your PATH",
                    f"Check if {base_cmd} is available with: which {base_cmd}",
                    "Verify your PATH environment variable",
                ]
            )

        elif "permission denied" in error.lower():
            suggestions.extend(
                [
                    f"Check file permissions for {base_cmd}",
                    "Try running with appropriate permissions",
                    "Verify you have execute permissions",
                ]
            )

        # Format the error message
        if suggestions:
            suggestion_text = "\n  • ".join(
                [""] + suggestions[:3]
            )  # Limit to 3 suggestions
            return f"[ERROR: {error_clean}]\n[Suggestions:{suggestion_text}]"
        else:
            return f"[ERROR: {error_clean}]"

    def extract_commands(self, text: str) -> List[Tuple[str, str]]:
        """
        Extract commands from text using various syntaxes:
        - $(command) - shell-like command substitution
        - {cmd:command} - custom command syntax
        - {exec:command} - alternative command syntax

        Returns:
            List of (placeholder, command) tuples
        """
        commands = []

        # Pattern for $(command)
        shell_pattern = r"\$\(([^)]+)\)"
        for match in re.finditer(shell_pattern, text):
            placeholder = match.group(0)
            command = match.group(1).strip()
            commands.append((placeholder, command))

        # Pattern for {cmd:command} or {exec:command}
        custom_pattern = r"\{(?:cmd|exec):([^}]+)\}"
        for match in re.finditer(custom_pattern, text):
            placeholder = match.group(0)
            command = match.group(1).strip()
            commands.append((placeholder, command))

        return commands

    def process_template(
        self, template: str, variables: Dict[str, str] = None
    ) -> Tuple[str, Dict[str, str]]:
        """
        Process a template by executing embedded commands and substituting variables.

        Args:
            template: Template string with embedded commands and variables
            variables: Dictionary of variable substitutions

        Returns:
            Tuple of (processed_template, command_outputs)
        """
        variables = variables or {}
        command_outputs = {}
        processed = template

        # Extract and execute commands
        commands = self.extract_commands(template)

        for placeholder, command in commands:
            if placeholder in command_outputs:
                # Already executed this command
                continue

            # Try command with intelligent fallbacks
            success, stdout, stderr = self.try_command_alternatives(command)

            if success:
                output = stdout.strip()
                command_outputs[placeholder] = output
                processed = processed.replace(placeholder, output)
            else:
                # Provide helpful error message with suggestions
                error_msg = self._format_intelligent_error(command, stderr)
                command_outputs[placeholder] = error_msg
                processed = processed.replace(placeholder, error_msg)

        # Substitute regular variables
        for var, value in variables.items():
            processed = processed.replace(f"{{{var}}}", value)

        return processed, command_outputs

    def get_command_info(self, command: str) -> Dict[str, str]:
        """Get information about a command (help text, version, etc.)."""
        info = {}

        if not self.is_command_allowed(command):
            info["error"] = f"Command disabled for security: {command}"
            return info

        # Try to get version
        for version_flag in ["--version", "-V", "-v", "version"]:
            success, stdout, stderr = self.execute_command(f"{command} {version_flag}")
            if success and stdout.strip():
                info["version"] = stdout.strip().split("\n")[0]
                break

        # Try to get help
        for help_flag in ["--help", "-h", "help"]:
            success, stdout, stderr = self.execute_command(f"{command} {help_flag}")
            if success and stdout.strip():
                info["help"] = stdout.strip()
                break

        return info
