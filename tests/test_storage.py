from aix.storage import PromptStorage
from aix.template import PromptTemplate


class TestPromptStorage:
    """Test prompt storage functionality without mocks."""

    def test_storage_initialization(self, temp_storage_dir):
        """Test storage initialization with custom directory."""
        storage = PromptStorage(temp_storage_dir)
        assert storage.storage_path == temp_storage_dir
        assert storage.storage_path.exists()

    def test_save_and_get_prompt_yaml(self, temp_storage_dir, sample_template):
        """Test saving and retrieving a prompt in YAML format."""
        storage = PromptStorage(temp_storage_dir)

        prompt = PromptTemplate(**sample_template)

        # Save prompt
        success = storage.save_prompt(prompt, "yaml")
        assert success is True

        # Verify files exist
        yaml_file = temp_storage_dir / "test-prompt.yaml"
        txt_file = temp_storage_dir / "test-prompt.txt"
        assert yaml_file.exists()
        assert txt_file.exists()

        # Verify content
        with open(txt_file) as f:
            assert sample_template["template"] in f.read()

        # Retrieve prompt
        retrieved = storage.get_prompt("test-prompt")
        assert retrieved is not None
        assert retrieved.name == sample_template["name"]
        assert retrieved.template == sample_template["template"]
        assert retrieved.description == sample_template["description"]
        assert retrieved.tags == sample_template["tags"]

    def test_save_and_get_prompt_json(self, temp_storage_dir, sample_template):
        """Test saving and retrieving a prompt in JSON format."""
        storage = PromptStorage(temp_storage_dir)

        prompt = PromptTemplate(**sample_template)

        # Save prompt
        success = storage.save_prompt(prompt, "json")
        assert success is True

        # Verify files exist
        json_file = temp_storage_dir / "test-prompt.json"
        txt_file = temp_storage_dir / "test-prompt.txt"
        assert json_file.exists()
        assert txt_file.exists()

        # Retrieve prompt
        retrieved = storage.get_prompt("test-prompt")
        assert retrieved is not None
        assert retrieved.name == sample_template["name"]

    def test_list_prompts(self, temp_storage_dir):
        """Test listing all available prompts."""
        storage = PromptStorage(temp_storage_dir)

        # Create multiple prompts
        prompts = [
            PromptTemplate("prompt1", "Template 1"),
            PromptTemplate("prompt2", "Template 2"),
            PromptTemplate("prompt3", "Template 3"),
        ]

        for prompt in prompts:
            storage.save_prompt(prompt)

        # List prompts
        listed = storage.list_prompts()
        assert len(listed) == 3

        names = [p.name for p in listed]
        assert "prompt1" in names
        assert "prompt2" in names
        assert "prompt3" in names

    def test_prompt_exists(self, temp_storage_dir):
        """Test checking if a prompt exists."""
        storage = PromptStorage(temp_storage_dir)

        prompt = PromptTemplate("existing", "Test template")
        storage.save_prompt(prompt)

        assert storage.prompt_exists("existing") is True
        assert storage.prompt_exists("nonexistent") is False

    def test_delete_prompt(self, temp_storage_dir):
        """Test deleting a prompt."""
        storage = PromptStorage(temp_storage_dir)

        prompt = PromptTemplate("to-delete", "Template to delete")
        storage.save_prompt(prompt)

        # Verify it exists
        assert storage.prompt_exists("to-delete") is True

        # Delete it
        success = storage.delete_prompt("to-delete")
        assert success is True

        # Verify it's gone
        assert storage.prompt_exists("to-delete") is False
        assert temp_storage_dir / "to-delete.yaml" not in temp_storage_dir.iterdir()
        assert temp_storage_dir / "to-delete.txt" not in temp_storage_dir.iterdir()

    def test_get_storage_info(self, temp_storage_dir):
        """Test getting storage information."""
        storage = PromptStorage(temp_storage_dir)

        # Create a prompt
        prompt = PromptTemplate("info-test", "Test template")
        storage.save_prompt(prompt)

        info = storage.get_storage_info()

        assert info["storage_path"] == str(temp_storage_dir)
        assert info["total_prompts"] == 1
        assert info["total_size_bytes"] > 0
        assert "yaml" in info["formats"]
        assert "json" in info["formats"]

    def test_get_nonexistent_prompt(self, temp_storage_dir):
        """Test getting a non-existent prompt."""
        storage = PromptStorage(temp_storage_dir)

        retrieved = storage.get_prompt("does-not-exist")
        assert retrieved is None

    def test_save_prompt_with_special_characters(self, temp_storage_dir):
        """Test saving prompts with special characters in template."""
        storage = PromptStorage(temp_storage_dir)

        special_template = """Hello {name},
This is a test with "quotes" and 'apostrophes'.
It also has newlines and tabs.
$(whoami) should execute a command.
{cmd:ls -la} is another command.
"""

        prompt = PromptTemplate(
            "special-chars",
            special_template,
            "Prompt with special characters",
            ["test", "special"],
        )

        success = storage.save_prompt(prompt)
        assert success is True

        retrieved = storage.get_prompt("special-chars")
        assert retrieved is not None
        assert retrieved.template == special_template
        assert retrieved.description == "Prompt with special characters"
