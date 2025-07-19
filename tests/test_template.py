import pytest
from aix.template import PromptTemplate, TemplateSafeEncoder


class TestPromptTemplate:
    """Test template engine functionality."""

    def test_template_creation(self):
        """Test basic template creation."""
        template = PromptTemplate(
            name="test",
            template="Hello {name}",
            description="A test template"
        )
        
        assert template.name == "test"
        assert template.template == "Hello {name}"
        assert template.description == "A test template"
        assert template.variables == ["name"]
        assert template.tags == []
        assert template.created_at is not None
        assert template.updated_at is not None

    def test_extract_variables_simple(self):
        """Test variable extraction from simple templates."""
        template = "Hello {name}, welcome to {place}!"
        variables = PromptTemplate.extract_variables(template)
        assert set(variables) == {"name", "place"}

    def test_extract_variables_with_commands(self):
        """Test variable extraction excludes command patterns."""
        template = "Hello {name}, your username is $(whoami) and path is {cmd:pwd}"
        variables = PromptTemplate.extract_variables(template)
        assert variables == ["name"]  # Only non-command variables

    def test_extract_variables_no_duplicates(self):
        """Test variable extraction removes duplicates."""
        template = "Hello {name}, {name} again, and {place}"
        variables = PromptTemplate.extract_variables(template)
        assert len(variables) == len(set(variables))
        assert set(variables) == {"name", "place"}

    def test_render_simple(self):
        """Test simple variable substitution."""
        template = PromptTemplate(
            name="simple",
            template="Hello {name}, welcome to {place}!"
        )
        
        variables = {"name": "Alice", "place": "Wonderland"}
        result = template.render_simple(variables)
        
        assert result == "Hello Alice, welcome to Wonderland!"

    def test_render_with_missing_variables(self):
        """Test rendering with missing variables."""
        template = PromptTemplate(
            name="missing",
            template="Hello {name}, your age is {age}"
        )
        
        variables = {"name": "Alice"}  # Missing age
        result = template.render_simple(variables)
        
        assert result == "Hello Alice, your age is {age}"

    def test_validate_variables_all_present(self):
        """Test variable validation with all variables provided."""
        template = PromptTemplate(
            name="validation",
            template="Hello {name}, welcome {place}"
        )
        
        variables = {"name": "Alice", "place": "here"}
        missing = template.validate_variables(variables)
        
        assert missing == []

    def test_validate_variables_missing(self):
        """Test variable validation with missing variables."""
        template = PromptTemplate(
            name="validation",
            template="Hello {name}, welcome {place}"
        )
        
        variables = {"name": "Alice"}
        missing = template.validate_variables(variables)
        
        assert missing == ["place"]

    def test_template_to_dict_and_back(self):
        """Test serialization and deserialization."""
        original = PromptTemplate(
            name="serial",
            template="Hello {name}",
            description="Test serialization",
            tags=["test", "serial"]
        )
        
        dict_data = original.to_dict()
        restored = PromptTemplate.from_dict(dict_data)
        
        assert restored.name == original.name
        assert restored.template == original.template
        assert restored.description == original.description
        assert restored.tags == original.tags

    def test_template_with_empty_fields(self):
        """Test template creation with empty optional fields."""
        template = PromptTemplate(
            name="minimal",
            template="Hello world"
        )
        
        assert template.description == ""
        assert template.tags == []
        assert template.variables == []

    def test_template_with_command_syntax(self):
        """Test template with various command syntaxes."""
        template = PromptTemplate(
            name="commands",
            template="User: $(whoami), Path: {cmd:pwd}, Date: {exec:date}"
        )
        
        assert template.variables == []  # No variables, only commands


class TestTemplateSafeEncoder:
    """Test template encoding utilities."""

    def test_escape_template(self):
        """Test template escaping for CLI usage."""
        original = "Hello\nWorld\tTab"
        escaped = TemplateSafeEncoder.escape_template(original)
        expected = "Hello\\nWorld\\tTab"
        assert escaped == expected

    def test_unescape_template(self):
        """Test template unescaping from CLI encoding."""
        escaped = "Hello\\nWorld\\tTab"
        unescaped = TemplateSafeEncoder.unescape_template(escaped)
        expected = "Hello\nWorld\tTab"
        assert unescaped == expected

    def test_round_trip_escaping(self):
        """Test escaping and unescaping preserves original content."""
        original = "Line1\nLine2\tTab\rReturn"
        escaped = TemplateSafeEncoder.escape_template(original)
        unescaped = TemplateSafeEncoder.unescape_template(escaped)
        assert unescaped == original

    def test_safe_shell_quote(self):
        """Test safe shell quoting."""
        text = 'Hello "world" with spaces'
        quoted = TemplateSafeEncoder.safe_shell_quote(text)
        # Should be JSON-like quoted
        assert quoted.startswith('"')
        assert quoted.endswith('"')
        # Check that the content is properly escaped
        assert 'Hello' in quoted and 'world' in quoted

    def test_format_for_cli(self):
        """Test complete CLI formatting."""
        template = "Hello\nWorld\t{variable}"
        formatted = TemplateSafeEncoder.format_for_cli(template)
        
        assert formatted.startswith('"')
        assert formatted.endswith('"')
        # Check that newline and tab are properly escaped
        assert "Hello" in formatted and "World" in formatted