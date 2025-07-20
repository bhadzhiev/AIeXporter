import re
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from .commands.executor import CommandExecutor


@dataclass
class PlaceholderGenerator:
    language: str
    script: str


@dataclass
class PromptTemplate:
    name: str
    template: str
    description: str = ""
    tags: List[str] = None
    variables: List[str] = None
    placeholder_generators: List[PlaceholderGenerator] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.variables is None:
            self.variables = self.extract_variables(self.template)
        if self.placeholder_generators is None:
            self.placeholder_generators = []
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
        execute_generators: bool = True,
    ) -> Tuple[str, Optional[Dict[str, str]]]:
        """
        Render the template with provided variables and optionally execute commands.

        Args:
            variables: Dictionary of variable substitutions
            execute_commands: Whether to execute embedded commands
            command_executor: CommandExecutor instance for running commands
            execute_generators: Whether to execute placeholder generators

        Returns:
            Tuple of (rendered_template, command_outputs or None)
        """
        # Start with the provided variables
        all_variables = dict(variables)
        
        # Execute placeholder generators if enabled
        if execute_generators and self.placeholder_generators:
            try:
                from .placeholder_generator import PlaceholderExecutor
                executor = PlaceholderExecutor()
                generated_placeholders = executor.execute_generators(self.placeholder_generators)
                
                # Merge generated placeholders with provided variables
                # Provided variables take precedence over generated ones
                for key, value in generated_placeholders.items():
                    if key not in all_variables:
                        all_variables[key] = value
                        
            except Exception as e:
                # Log warning but continue with template rendering
                print(f"Warning: Placeholder generation failed: {e}")
        
        if execute_commands and command_executor:
            # Use command executor to process template with commands
            result, command_outputs = command_executor.process_template(
                self.template, all_variables
            )
            return result, command_outputs
        else:
            # Standard variable substitution only
            result = self.template
            for var, value in all_variables.items():
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
        # Handle placeholder_generators conversion
        generators_data = data.get('placeholder_generators', [])
        if generators_data:
            generators = []
            for gen_data in generators_data:
                if isinstance(gen_data, dict):
                    generators.append(PlaceholderGenerator(**gen_data))
                elif isinstance(gen_data, PlaceholderGenerator):
                    generators.append(gen_data)
            data = dict(data)  # Make a copy
            data['placeholder_generators'] = generators
        
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
        
        # Placeholder generators
        if self.placeholder_generators:
            generators_elem = ET.SubElement(metadata, "placeholder_generators")
            for generator in self.placeholder_generators:
                gen_elem = ET.SubElement(generators_elem, "placeholder_generator")
                gen_elem.set("language", generator.language)
                gen_elem.text = f"PLACEHOLDER_GENERATOR_CDATA_{generator.language}"
        
        # Content section - will be replaced with CDATA manually
        content = ET.SubElement(root, "content")
        content.text = "PLACEHOLDER_FOR_CDATA"
        
        # Format XML string with pretty printing
        ET.indent(root, space="  ", level=0)
        xml_string = '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding='unicode')
        
        # Replace placeholder with CDATA section
        cdata_content = f"<![CDATA[{self.template}]]>"
        xml_string = xml_string.replace("PLACEHOLDER_FOR_CDATA", cdata_content)
        
        # Replace placeholder generator CDATA sections
        if self.placeholder_generators:
            for generator in self.placeholder_generators:
                placeholder = f"PLACEHOLDER_GENERATOR_CDATA_{generator.language}"
                cdata_script = f"<![CDATA[{generator.script}]]>"
                xml_string = xml_string.replace(placeholder, cdata_script)
        
        return xml_string

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
            
            # Extract placeholder generators
            placeholder_generators = []
            generators_elem = metadata.find("placeholder_generators")
            if generators_elem is not None:
                for gen_elem in generators_elem.findall("placeholder_generator"):
                    language = gen_elem.get("language", "")
                    script = gen_elem.text or ""
                    if language and script:
                        placeholder_generators.append(PlaceholderGenerator(language=language, script=script))
            
            # Extract content (handle both CDATA and regular text)
            content_elem = root.find("content")
            if content_elem is not None:
                # Handle CDATA content
                if content_elem.text and content_elem.text.strip():
                    template = content_elem.text
                else:
                    # If no text, check for CDATA in the original XML
                    # This handles cases where CDATA might not be parsed as text
                    template = ""
                    # Find the content section in the raw XML
                    import re
                    content_match = re.search(r'<content><!\[CDATA\[(.*?)\]\]></content>', xml_content, re.DOTALL)
                    if content_match:
                        template = content_match.group(1)
                    elif content_elem.text:
                        template = content_elem.text
            else:
                template = ""
            
            return cls(
                name=name,
                template=template,
                description=description,
                tags=tags,
                variables=variables,
                placeholder_generators=placeholder_generators,
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
