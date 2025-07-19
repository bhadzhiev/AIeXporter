import re
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from .command_executor import CommandExecutor


@dataclass
class PromptTemplate:
    name: str
    template: str
    description: str = ""
    tags: List[str] = None
    variables: List[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.variables is None:
            self.variables = self.extract_variables(self.template)
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    @staticmethod
    def extract_variables(template: str) -> List[str]:
        """Extract variable names from template using {variable} syntax, excluding commands."""
        # Extract all {something} patterns
        pattern = r"\{([^}]+)\}"
        all_matches = re.findall(pattern, template)

        # Filter out command patterns
        variables = []
        for match in all_matches:
            # Skip command patterns like cmd:something, exec:something
            if not (match.startswith("cmd:") or match.startswith("exec:")):
                variables.append(match)

        # Also exclude $(...) shell command patterns from variable extraction
        return list(set(variables))  # Remove duplicates

    def render(
        self,
        variables: Dict[str, str],
        execute_commands: bool = False,
        command_executor: Optional[CommandExecutor] = None,
    ) -> Tuple[str, Optional[Dict[str, str]]]:
        """
        Render the template with provided variables and optionally execute commands.

        Args:
            variables: Dictionary of variable substitutions
            execute_commands: Whether to execute embedded commands
            command_executor: CommandExecutor instance for running commands

        Returns:
            Tuple of (rendered_template, command_outputs or None)
        """
        if execute_commands and command_executor:
            # Use command executor to process template with commands
            result, command_outputs = command_executor.process_template(
                self.template, variables
            )
            return result, command_outputs
        else:
            # Standard variable substitution only
            result = self.template
            for var, value in variables.items():
                result = result.replace(f"{{{var}}}", value)
            return result, None

    def render_simple(self, variables: Dict[str, str]) -> str:
        """Simple render method for backward compatibility."""
        result, _ = self.render(variables, execute_commands=False)
        return result

    def validate_variables(self, variables: Dict[str, str]) -> List[str]:
        """Check if all required variables are provided. Returns list of missing variables."""
        provided_vars = set(variables.keys())
        required_vars = set(self.variables)
        missing = required_vars - provided_vars
        return list(missing)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "PromptTemplate":
        """Create instance from dictionary."""
        return cls(**data)


class TemplateSafeEncoder:
    """Utility for safely encoding template strings to handle quotes, newlines, etc."""

    @staticmethod
    def escape_template(template: str) -> str:
        """
        Escape a template string for safe CLI usage.
        Handles quotes, newlines, and special characters.
        """
        # Replace newlines with literal \n
        template = template.replace("\n", "\\n")

        # Replace tabs with literal \t
        template = template.replace("\t", "\\t")

        # Replace carriage returns
        template = template.replace("\r", "\\r")

        # Escape backslashes (but not the ones we just added)
        template = re.sub(r"(?<!\\)\\(?![ntr])", r"\\\\", template)

        return template

    @staticmethod
    def unescape_template(template: str) -> str:
        """
        Unescape a template string from CLI encoding.
        Converts literal escape sequences back to actual characters.
        """
        # Convert literal escape sequences back
        template = template.replace("\\n", "\n")
        template = template.replace("\\t", "\t")
        template = template.replace("\\r", "\r")
        template = template.replace("\\\\", "\\")

        return template

    @staticmethod
    def safe_shell_quote(text: str) -> str:
        """
        Safely quote text for shell usage.
        Uses JSON encoding to handle all special characters.
        """
        return json.dumps(text)

    @staticmethod
    def format_for_cli(template: str) -> str:
        """
        Format template for safe CLI usage with proper quoting.
        """
        # First escape the template
        escaped = TemplateSafeEncoder.escape_template(template)

        # Then quote it safely for shell
        return TemplateSafeEncoder.safe_shell_quote(escaped)
