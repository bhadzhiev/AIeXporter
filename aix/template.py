import re
import json
import xml.etree.ElementTree as ET
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

    def to_xml(self) -> str:
        """Convert to XML format."""
        root = ET.Element("template")
        
        # Metadata section
        metadata = ET.SubElement(root, "metadata")
        
        # Basic fields
        ET.SubElement(metadata, "name").text = self.name
        ET.SubElement(metadata, "description").text = self.description or ""
        ET.SubElement(metadata, "created_at").text = self.created_at or ""
        ET.SubElement(metadata, "updated_at").text = self.updated_at or ""
        
        # Tags
        if self.tags:
            tags_elem = ET.SubElement(metadata, "tags")
            for tag in self.tags:
                ET.SubElement(tags_elem, "tag").text = tag
        
        # Variables
        if self.variables:
            variables_elem = ET.SubElement(metadata, "variables")
            for var in self.variables:
                ET.SubElement(variables_elem, "variable").text = var
        
        # Content section using CDATA
        content = ET.SubElement(root, "content")
        content.text = self.template
        
        # Format and return XML string with pretty printing
        ET.indent(root, space="  ", level=0)
        return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding='unicode')

    @classmethod
    def from_xml(cls, xml_content: str) -> "PromptTemplate":
        """Create instance from XML content."""
        try:
            root = ET.fromstring(xml_content)
            
            # Extract metadata
            metadata = root.find("metadata")
            if metadata is None:
                raise ValueError("Invalid XML: missing metadata section")
            
            name = metadata.find("name")
            name = name.text if name is not None else ""
            
            description = metadata.find("description")
            description = description.text if description is not None else ""
            
            created_at = metadata.find("created_at")
            created_at = created_at.text if created_at is not None else None
            
            updated_at = metadata.find("updated_at")
            updated_at = updated_at.text if updated_at is not None else None
            
            # Extract tags
            tags = []
            tags_elem = metadata.find("tags")
            if tags_elem is not None:
                for tag_elem in tags_elem.findall("tag"):
                    if tag_elem.text:
                        tags.append(tag_elem.text)
            
            # Extract variables
            variables = []
            variables_elem = metadata.find("variables")
            if variables_elem is not None:
                for var_elem in variables_elem.findall("variable"):
                    if var_elem.text:
                        variables.append(var_elem.text)
            
            # Extract content
            content_elem = root.find("content")
            template = content_elem.text if content_elem is not None else ""
            
            return cls(
                name=name,
                template=template,
                description=description,
                tags=tags,
                variables=variables,
                created_at=created_at,
                updated_at=updated_at
            )
            
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML format: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing XML template: {e}")


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
