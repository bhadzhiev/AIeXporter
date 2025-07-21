import re
import shlex
from typing import List, Optional
from .base import SecurityValidator


class DefaultSecurityValidator(SecurityValidator):
    """Default security validator with built-in dangerous command patterns."""

    def __init__(self, disabled_commands: Optional[List[str]] = None):
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
            "wget",
            "curl",
            "ssh",
            "scp",
            "ftp",
            "sftp",
            "nc",
            "netcat",
            "telnet",
        ]

        self.dangerous_patterns = [
            r"rm\s+-rf\s+/",
            r":\(\)\s*\{\s*:\|:\&\s*\}\s*;\s*:",
            r"\>\s*/dev/sd[a-z]",
            r"dd\s+.*of\s*=\s*/dev/",
            r"chmod\s+777\s+/",
            r"chown\s+.*\s+/",
            r"\|\s*sh\s*$",
            r"\$\(.*\$\(.*\).*\)",
            r"^\s*eval\s+",
            r"^\s*exec\s+",
            r"^\s*source\s+",
            r"^\s*\.\s+",
            r"mv\s+.*\s+/",
            r"cp\s+.*\s+/\s*$",
            r"rsync\s+.*\s+/\s*$",
        ]

    def is_allowed(self, command: str) -> bool:
        """Check if command is allowed to be executed."""
        if not command.strip():
            return False

        try:
            parsed = shlex.split(command)
            if not parsed:
                return False

            base_command = parsed[0]
            command_lower = command.lower().strip()

            # Check disabled commands
            for disabled in self.disabled_commands:
                if base_command == disabled:
                    return False
                if base_command.startswith(disabled + " ") or base_command.startswith(
                    disabled + "\t"
                ):
                    return False
                if (
                    disabled.endswith(" /")
                    or disabled.startswith(":")
                    or disabled == "."
                ):
                    if disabled in command_lower:
                        return False

            # Check dangerous patterns
            for pattern in self.dangerous_patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    return False

            return True

        except ValueError:
            return False

    def get_error_message(self, command: str) -> str:
        """Get error message for disallowed command."""
        return f"Command disabled for security: {command}"


class CompositeSecurityValidator(SecurityValidator):
    """Composite validator that combines multiple security validators."""

    def __init__(self, validators: List[SecurityValidator]):
        self.validators = validators

    def is_allowed(self, command: str) -> bool:
        """Check if all validators allow the command."""
        return all(validator.is_allowed(command) for validator in self.validators)

    def get_error_message(self, command: str) -> str:
        """Get error message from first failing validator."""
        for validator in self.validators:
            if not validator.is_allowed(command):
                return validator.get_error_message(command)
        return "Command not allowed"
