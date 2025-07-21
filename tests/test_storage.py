from aix.storage import PromptStorage
from aix.template import PromptTemplate


class TestPromptStorage:
    """Test prompt storage functionality without mocks."""

    def test_storage_initialization(self, temp_storage_dir):
        """Test storage initialization with custom directory."""
        storage = PromptStorage(temp_storage_dir)
        assert storage.storage_path == temp_storage_dir
        assert storage.storage_path.exists()

    def test_save_and_get_prompt_xml(self, temp_storage_dir, sample_template):
        """Test saving and retrieving a prompt in collections-only XML format."""
        storage = PromptStorage(temp_storage_dir)

        prompt = PromptTemplate(**sample_template)

        # Save prompt (goes to default collection)
        success = storage.save_prompt(prompt)
        assert success is True

        # Verify default collection XML file exists
        default_collection_xml = temp_storage_dir / "collections" / "default.xml"
        assert default_collection_xml.exists()

        # Verify content contains template text in the collection XML
        with open(default_collection_xml, encoding="utf-8") as f:
            xml_content = f.read()
            assert sample_template["template"] in xml_content
            assert sample_template["name"] in xml_content
            assert sample_template["description"] in xml_content

        # Retrieve prompt
        retrieved = storage.get_prompt("test-prompt")
        assert retrieved is not None
        assert retrieved.name == sample_template["name"]
        assert retrieved.template == sample_template["template"]
        assert retrieved.description == sample_template["description"]
        assert retrieved.tags == sample_template["tags"]

    def test_save_and_get_prompt_with_collection(
        self, temp_storage_dir, sample_template
    ):
        """Test saving and retrieving a prompt in a collection."""
        storage = PromptStorage(temp_storage_dir)

        prompt = PromptTemplate(**sample_template)

        # Save prompt in a collection
        success = storage.save_prompt_xml(prompt, "test-collection")
        assert success is True

        # Verify collection XML file exists (not individual template files)
        collection_xml = temp_storage_dir / "collections" / "test-collection.xml"
        assert collection_xml.exists()

        # Retrieve prompt from collection
        retrieved = storage.get_prompt("test-prompt", "test-collection")
        assert retrieved is not None
        assert retrieved.name == sample_template["name"]
        assert retrieved.template == sample_template["template"]

    def test_list_prompts(self, temp_storage_dir):
        """Test listing all available prompts in collections-only mode."""
        storage = PromptStorage(temp_storage_dir)

        # Create multiple prompts (all go to default collection)
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
        assert temp_storage_dir / "to-delete.xml" not in temp_storage_dir.iterdir()

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
        assert info["storage_type"] == "collections_only"
        assert info["default_collection"] == "default"
        assert info["collections"] == 1

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
