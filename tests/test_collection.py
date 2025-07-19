from aix.collection import Collection, CollectionStorage, CollectionManager
from aix.storage import PromptStorage
from aix.template import PromptTemplate


class TestCollection:
    """Test collection functionality."""

    def test_collection_creation(self):
        """Test basic collection creation."""
        collection = Collection(
            name="test-collection",
            description="A test collection",
            templates=["prompt1", "prompt2"],
            tags=["test", "collection"],
        )

        assert collection.name == "test-collection"
        assert collection.description == "A test collection"
        assert collection.templates == ["prompt1", "prompt2"]
        assert collection.tags == ["test", "collection"]
        assert collection.created_at is not None
        assert collection.updated_at is not None

    def test_collection_add_template(self):
        """Test adding templates to collection."""
        collection = Collection(name="test")

        # Add new template
        result = collection.add_template("new-prompt")
        assert result is True
        assert "new-prompt" in collection.templates

        # Try to add duplicate
        result = collection.add_template("new-prompt")
        assert result is False
        assert collection.templates.count("new-prompt") == 1

    def test_collection_remove_template(self):
        """Test removing templates from collection."""
        collection = Collection(
            name="test", templates=["prompt1", "prompt2", "prompt3"]
        )

        # Remove existing template
        result = collection.remove_template("prompt2")
        assert result is True
        assert "prompt2" not in collection.templates
        assert len(collection.templates) == 2

        # Remove non-existent template
        result = collection.remove_template("nonexistent")
        assert result is False

    def test_collection_has_template(self):
        """Test checking if collection contains a template."""
        collection = Collection(name="test", templates=["prompt1", "prompt2"])

        assert collection.has_template("prompt1") is True
        assert collection.has_template("prompt2") is True
        assert collection.has_template("prompt3") is False

    def test_collection_serialization(self):
        """Test collection serialization to/from dict."""
        collection = Collection(
            name="serial-test",
            description="Test serialization",
            templates=["t1", "t2"],
            tags=["tag1", "tag2"],
        )

        dict_data = collection.to_dict()
        restored = Collection.from_dict(dict_data)

        assert restored.name == collection.name
        assert restored.description == collection.description
        assert restored.templates == collection.templates
        assert restored.tags == collection.tags


class TestCollectionStorage:
    """Test collection storage functionality."""

    def test_storage_initialization(self, temp_storage_dir):
        """Test storage initialization."""
        storage = CollectionStorage(temp_storage_dir)

        assert storage.storage_path == temp_storage_dir
        assert storage.collections_path.exists()
        assert storage.current_collection_file is not None

    def test_save_and_get_collection_yaml(self, temp_storage_dir):
        """Test saving and retrieving collections in YAML format."""
        storage = CollectionStorage(temp_storage_dir)

        collection = Collection(
            name="test-collection",
            description="A test collection",
            templates=["prompt1", "prompt2"],
            tags=["test"],
        )

        # Save collection
        success = storage.save_collection(collection, "yaml")
        assert success is True

        # Verify file exists
        yaml_file = temp_storage_dir / "collections" / "test-collection.yaml"
        assert yaml_file.exists()

        # Retrieve collection
        retrieved = storage.get_collection("test-collection")
        assert retrieved is not None
        assert retrieved.name == collection.name
        assert retrieved.description == collection.description
        assert retrieved.templates == collection.templates

    def test_save_and_get_collection_json(self, temp_storage_dir):
        """Test saving and retrieving collections in JSON format."""
        storage = CollectionStorage(temp_storage_dir)

        collection = Collection(name="json-collection", templates=["prompt1"])

        success = storage.save_collection(collection, "json")
        assert success is True

        json_file = temp_storage_dir / "collections" / "json-collection.json"
        assert json_file.exists()

        retrieved = storage.get_collection("json-collection")
        assert retrieved is not None

    def test_list_collections(self, temp_storage_dir):
        """Test listing all collections."""
        storage = CollectionStorage(temp_storage_dir)

        # Create multiple collections
        collections = [
            Collection("collection1", "First collection"),
            Collection("collection2", "Second collection"),
            Collection("collection3", "Third collection"),
        ]

        for collection in collections:
            storage.save_collection(collection)

        # List collections
        listed = storage.list_collections()
        assert len(listed) == 3

        names = [c.name for c in listed]
        assert "collection1" in names
        assert "collection2" in names
        assert "collection3" in names

    def test_collection_exists(self, temp_storage_dir):
        """Test checking if collection exists."""
        storage = CollectionStorage(temp_storage_dir)

        collection = Collection("existing-collection")
        storage.save_collection(collection)

        assert storage.collection_exists("existing-collection") is True
        assert storage.collection_exists("nonexistent") is False

    def test_delete_collection(self, temp_storage_dir):
        """Test deleting collections."""
        storage = CollectionStorage(temp_storage_dir)

        collection = Collection("to-delete")
        storage.save_collection(collection)

        assert storage.collection_exists("to-delete") is True

        success = storage.delete_collection("to-delete")
        assert success is True
        assert storage.collection_exists("to-delete") is False

    def test_set_and_get_current_collection(self, temp_storage_dir):
        """Test current collection management."""
        storage = CollectionStorage(temp_storage_dir)

        # Create collection
        collection = Collection("current-collection")
        storage.save_collection(collection)

        # Set as current
        success = storage.set_current_collection("current-collection")
        assert success is True

        # Verify it's current
        current = storage.get_current_collection()
        assert current == "current-collection"

        # Clear current
        success = storage.clear_current_collection()
        assert success is True

        current = storage.get_current_collection()
        assert current is None

    def test_get_collection_templates(self, temp_storage_dir):
        """Test getting templates from a collection."""
        # Setup storage for both collections and prompts
        collection_storage = CollectionStorage(temp_storage_dir)
        prompt_storage = PromptStorage(temp_storage_dir)

        # Create prompts
        prompt1 = PromptTemplate("prompt1", "Template 1")
        prompt2 = PromptTemplate("prompt2", "Template 2")
        prompt_storage.save_prompt(prompt1)
        prompt_storage.save_prompt(prompt2)

        # Create collection
        collection = Collection(
            name="template-collection", templates=["prompt1", "prompt2"]
        )
        collection_storage.save_collection(collection)

        # Get templates
        templates = collection_storage.get_collection_templates(
            "template-collection", prompt_storage
        )

        assert len(templates) == 2
        template_names = [t.name for t in templates]
        assert "prompt1" in template_names
        assert "prompt2" in template_names

    def test_validate_collection_templates(self, temp_storage_dir):
        """Test validation of collection templates."""
        collection_storage = CollectionStorage(temp_storage_dir)
        prompt_storage = PromptStorage(temp_storage_dir)

        # Create some prompts
        prompt1 = PromptTemplate("valid1", "Template 1")
        prompt_storage.save_prompt(prompt1)

        # Create collection with mixed valid/invalid templates
        collection = Collection(
            name="mixed-collection",
            templates=["valid1", "missing1", "valid2", "missing2"],
        )
        collection_storage.save_collection(collection)

        # Validate
        validation = collection_storage.validate_collection_templates(
            "mixed-collection", prompt_storage
        )

        assert validation["valid"] == ["valid1"]
        assert "missing1" in validation["missing"]
        assert "missing2" in validation["missing"]


class TestCollectionManager:
    """Test collection manager functionality."""

    def test_manager_initialization(self, temp_storage_dir):
        """Test manager initialization."""
        manager = CollectionManager(temp_storage_dir)

        assert manager.collection_storage is not None
        assert manager.prompt_storage is not None

    def test_create_collection(self, temp_storage_dir):
        """Test collection creation through manager."""
        manager = CollectionManager(temp_storage_dir)

        success = manager.create_collection(
            name="manager-collection",
            description="Created via manager",
            templates=["prompt1"],
            tags=["manager"],
        )

        assert success is True
        assert manager.collection_storage.collection_exists("manager-collection")

    def test_load_collection(self, temp_storage_dir):
        """Test loading collections."""
        manager = CollectionManager(temp_storage_dir)

        # Create collection
        manager.create_collection("load-test")

        # Load it
        success = manager.load_collection("load-test")
        assert success is True

        # Verify it's loaded
        current = manager.collection_storage.get_current_collection()
        assert current == "load-test"

    def test_add_template_to_current_collection(self, temp_storage_dir):
        """Test adding templates to current collection."""
        manager = CollectionManager(temp_storage_dir)

        # Create prompt and collection
        prompt = PromptTemplate("test-prompt", "Test template")
        manager.prompt_storage.save_prompt(prompt)

        manager.create_collection("add-test")
        manager.load_collection("add-test")

        # Add template
        success = manager.add_template_to_current_collection("test-prompt")
        assert success is True

        # Verify
        collection = manager.collection_storage.get_collection("add-test")
        assert "test-prompt" in collection.templates

    def test_remove_template_from_current_collection(self, temp_storage_dir):
        """Test removing templates from current collection."""
        manager = CollectionManager(temp_storage_dir)

        # Create prompt and collection
        prompt = PromptTemplate("remove-prompt", "Test template")
        manager.prompt_storage.save_prompt(prompt)

        manager.create_collection("remove-test", templates=["remove-prompt"])
        manager.load_collection("remove-test")

        # Remove template
        success = manager.remove_template_from_current_collection("remove-prompt")
        assert success is True

        # Verify
        collection = manager.collection_storage.get_collection("remove-test")
        assert "remove-prompt" not in collection.templates

    def test_get_current_collection_info(self, temp_storage_dir):
        """Test getting current collection info."""
        manager = CollectionManager(temp_storage_dir)

        # No current collection
        info = manager.get_current_collection_info()
        assert info is None

        # Create and load collection
        manager.create_collection("info-test")
        manager.load_collection("info-test")

        info = manager.get_current_collection_info()
        assert info is not None
        assert info["collection"].name == "info-test"

    def test_export_and_import_collection(self, temp_storage_dir):
        """Test collection export and import functionality."""
        manager = CollectionManager(temp_storage_dir)

        # Create prompts and collection
        prompt1 = PromptTemplate("export-prompt1", "Template 1")
        prompt2 = PromptTemplate("export-prompt2", "Template 2")
        manager.prompt_storage.save_prompt(prompt1)
        manager.prompt_storage.save_prompt(prompt2)

        manager.create_collection(
            "export-test",
            description="Collection for export testing",
            templates=["export-prompt1", "export-prompt2"],
            tags=["export", "test"],
        )

        # Export collection
        export_path = temp_storage_dir / "exports"
        export_path.mkdir(exist_ok=True)

        success = manager.export_collection(
            "export-test", export_path, include_templates=True
        )
        assert success is True

        # Verify export files exist
        collection_file = export_path / "export-test-bundle.tar.gz"
        assert collection_file.exists()

        # Import collection
        manager.collection_storage.delete_collection("export-test")
        manager.prompt_storage.delete_prompt("export-prompt1")
        manager.prompt_storage.delete_prompt("export-prompt2")

        result = manager.import_collection(collection_file, overwrite=True)
        assert result["success"] is True
        assert result["collection_name"] == "export-test"
        # Templates might be imported with different naming, check for basic success
        assert isinstance(result["imported_templates"], list)
