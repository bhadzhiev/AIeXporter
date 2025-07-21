import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from .template import PromptTemplate


class PromptStorage:
    """Collections-only storage system. All templates are stored within collections."""

    DEFAULT_COLLECTION = "default"

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize storage with custom path or default ~/.prompts"""
        if storage_path:
            self.storage_path = storage_path
        else:
            # Check environment variable first, then fall back to default
            env_path = os.environ.get("AIX_STORAGE_PATH")
            if env_path:
                self.storage_path = Path(env_path)
            else:
                self.storage_path = Path.home() / ".prompts"
        self.storage_path.mkdir(exist_ok=True)
        self.collections_path = self.storage_path / "collections"
        self.collections_path.mkdir(exist_ok=True)

        # Ensure default collection exists
        self._ensure_default_collection()

    def _ensure_default_collection(self):
        """Ensure the default collection exists for ungrouped templates."""
        from .collection import CollectionStorage, Collection
        from datetime import datetime

        collection_storage = CollectionStorage(self.storage_path)
        if not collection_storage.collection_exists(self.DEFAULT_COLLECTION):
            default_collection = Collection(
                name=self.DEFAULT_COLLECTION,
                description="Default collection for ungrouped templates",
                templates=[],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
            )
            collection_storage.save_collection(default_collection)

    def _get_collection_for_template(self, template_name: str) -> Optional[str]:
        """Find which collection contains the given template."""
        from .collection import CollectionStorage

        collection_storage = CollectionStorage(self.storage_path)

        # Check all collections for the template
        for collection_xml in self.collections_path.glob("*.xml"):
            collection_name = collection_xml.stem
            collection = collection_storage.get_collection(collection_name)
            if collection and template_name in collection.templates:
                return collection_name
        return None

    def save_prompt(self, prompt: PromptTemplate, collection: str = None) -> bool:
        """Save a prompt template to a collection (collections-only storage)."""
        return self.save_prompt_xml(prompt, collection)

    def save_prompt_xml(self, prompt: PromptTemplate, collection: str = None) -> bool:
        """Save a prompt template to a collection as XML."""
        try:
            # Use default collection if none specified
            target_collection = collection or self.DEFAULT_COLLECTION

            # Remove from any existing collection first
            existing_collection = self._get_collection_for_template(prompt.name)
            if existing_collection and existing_collection != target_collection:
                self.delete_prompt(prompt.name)

            from .collection import CollectionManager

            manager = CollectionManager(self.storage_path)

            # Ensure target collection exists
            manager.ensure_collection_exists(
                target_collection,
                "Default collection for ungrouped templates"
                if target_collection == self.DEFAULT_COLLECTION
                else "",
            )

            # Add template to collection (this will save it as an embedded template)
            return manager.add_template_to_collection(target_collection, prompt)

        except Exception as e:
            print(f"Error saving XML prompt: {e}")
            return False

    def get_prompt(self, name: str, collection: str = None) -> Optional[PromptTemplate]:
        """Load a prompt template from collections (collections-only storage)."""
        # If collection is specified, try to get from that collection
        if collection:
            return self._get_prompt_from_collection_xml(name, collection)

        # Search all collections for the template
        if self.collections_path.exists():
            for collection_xml in self.collections_path.glob("*.xml"):
                collection_name = collection_xml.stem
                prompt = self._get_prompt_from_collection_xml(name, collection_name)
                if prompt:
                    return prompt

        return None

    def _get_prompt_from_collection_xml(
        self, name: str, collection: str
    ) -> Optional[PromptTemplate]:
        """Load a prompt template from collection XML file."""
        try:
            from .collection import CollectionStorage

            collection_storage = CollectionStorage(self.storage_path)
            return collection_storage.get_xml_collection_template(collection, name)
        except Exception as e:
            print(f"Error loading prompt {name} from collection {collection}: {e}")
            return None

    def list_prompts(self) -> List[PromptTemplate]:
        """List all available prompt templates from collections."""
        prompts = []
        seen_names = set()

        # Check all collections for templates
        if self.collections_path.exists():
            from .collection import CollectionStorage

            collection_storage = CollectionStorage(self.storage_path)

            for collection_xml in self.collections_path.glob("*.xml"):
                collection_name = collection_xml.stem
                collection = collection_storage.get_collection(collection_name)
                if collection:
                    for template_name in collection.templates:
                        if template_name in seen_names:
                            continue
                        seen_names.add(template_name)

                        prompt = self._get_prompt_from_collection_xml(
                            template_name, collection_name
                        )
                        if prompt:
                            prompts.append(prompt)

        return sorted(prompts, key=lambda p: p.name)

    def delete_prompt(self, name: str, collection: str = None) -> bool:
        """Delete a prompt template from collections."""
        if collection:
            # Delete from specific collection
            try:
                from .collection import CollectionManager

                manager = CollectionManager(self.storage_path)
                return manager.remove_template_from_collection(collection, name)
            except Exception as e:
                print(
                    f"Error deleting template {name} from collection {collection}: {e}"
                )
                return False
        else:
            # Find and remove from any collection
            target_collection = self._get_collection_for_template(name)
            if target_collection:
                try:
                    from .collection import CollectionManager

                    manager = CollectionManager(self.storage_path)
                    return manager.remove_template_from_collection(
                        target_collection, name
                    )
                except Exception as e:
                    print(
                        f"Error deleting template {name} from collection {target_collection}: {e}"
                    )

            return False

    def prompt_exists(self, name: str, collection: str = None) -> bool:
        """Check if a prompt with given name exists in collections."""
        if collection:
            # Check in specific collection
            return self._get_prompt_from_collection_xml(name, collection) is not None
        else:
            # Search all collections
            if self.collections_path.exists():
                for collection_xml in self.collections_path.glob("*.xml"):
                    collection_name = collection_xml.stem
                    if self._get_prompt_from_collection_xml(name, collection_name):
                        return True
        return False

    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about the storage location and contents."""
        prompts = self.list_prompts()

        # Calculate total size of collection XML files
        total_size = 0
        collections_count = 0

        # Collections directory XML files only
        if self.collections_path.exists():
            for f in self.collections_path.glob("*.xml"):
                total_size += f.stat().st_size
                collections_count += 1

        return {
            "storage_path": str(self.storage_path),
            "total_prompts": len(prompts),
            "total_size_bytes": total_size,
            "collections": collections_count,
            "storage_type": "collections_only",
            "default_collection": self.DEFAULT_COLLECTION,
        }
