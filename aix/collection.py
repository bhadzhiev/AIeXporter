"""Collection management for organizing prompt templates."""

import json
import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, asdict
from .template import PromptTemplate
from .storage import PromptStorage


@dataclass
class Collection:
    """Represents a collection of prompt templates."""
    name: str
    description: str = ""
    templates: List[str] = None  # List of template names
    tags: List[str] = None
    author: str = ""
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if self.templates is None:
            self.templates = []
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert collection to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Collection':
        """Create collection from dictionary."""
        return cls(**data)
    
    def add_template(self, template_name: str) -> bool:
        """Add a template to the collection."""
        if template_name not in self.templates:
            self.templates.append(template_name)
            return True
        return False
    
    def remove_template(self, template_name: str) -> bool:
        """Remove a template from the collection."""
        if template_name in self.templates:
            self.templates.remove(template_name)
            return True
        return False
    
    def has_template(self, template_name: str) -> bool:
        """Check if collection contains a template."""
        return template_name in self.templates


class CollectionStorage:
    """Manages storage and retrieval of collections."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize collection storage."""
        self.storage_path = storage_path or Path.home() / ".prompts"
        self.collections_path = self.storage_path / "collections"
        self.collections_path.mkdir(exist_ok=True)
        
        # File to track the currently loaded collection
        self.current_collection_file = self.storage_path / ".current_collection"
    
    def _get_collection_path(self, name: str, format: str = "yaml") -> Path:
        """Get the file path for a collection."""
        extension = "yaml" if format == "yaml" else "json"
        return self.collections_path / f"{name}.{extension}"
    
    def save_collection(self, collection: Collection, format: str = "yaml") -> bool:
        """Save a collection to storage."""
        try:
            collection_path = self._get_collection_path(collection.name, format)
            data = collection.to_dict()
            
            if format == "yaml":
                with open(collection_path, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            else:  # json
                with open(collection_path, 'w') as f:
                    json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving collection: {e}")
            return False
    
    def get_collection(self, name: str) -> Optional[Collection]:
        """Load a collection from storage."""
        for format in ["yaml", "json"]:
            collection_path = self._get_collection_path(name, format)
            if collection_path.exists():
                try:
                    if format == "yaml":
                        with open(collection_path, 'r') as f:
                            data = yaml.safe_load(f)
                    else:  # json
                        with open(collection_path, 'r') as f:
                            data = json.load(f)
                    
                    return Collection.from_dict(data)
                except Exception as e:
                    print(f"Error loading collection {name}: {e}")
                    continue
        
        return None
    
    def list_collections(self) -> List[Collection]:
        """List all available collections."""
        collections = []
        seen_names = set()
        
        for file_path in self.collections_path.glob("*"):
            if file_path.suffix in [".yaml", ".yml", ".json"]:
                name = file_path.stem
                if name in seen_names:
                    continue
                seen_names.add(name)
                
                collection = self.get_collection(name)
                if collection:
                    collections.append(collection)
        
        return sorted(collections, key=lambda c: c.name)
    
    def delete_collection(self, name: str) -> bool:
        """Delete a collection from storage."""
        deleted = False
        
        for format in ["yaml", "json"]:
            collection_path = self._get_collection_path(name, format)
            if collection_path.exists():
                try:
                    collection_path.unlink()
                    deleted = True
                except Exception as e:
                    print(f"Error deleting {collection_path}: {e}")
        
        # Clear current collection if it was the deleted one
        if self.get_current_collection() == name:
            self.clear_current_collection()
        
        return deleted
    
    def collection_exists(self, name: str) -> bool:
        """Check if a collection exists."""
        for format in ["yaml", "json"]:
            if self._get_collection_path(name, format).exists():
                return True
        return False
    
    def set_current_collection(self, name: str) -> bool:
        """Set the current active collection."""
        if self.collection_exists(name):
            try:
                with open(self.current_collection_file, 'w') as f:
                    f.write(name)
                return True
            except Exception as e:
                print(f"Error setting current collection: {e}")
        return False
    
    def get_current_collection(self) -> Optional[str]:
        """Get the name of the current active collection."""
        if self.current_collection_file.exists():
            try:
                with open(self.current_collection_file, 'r') as f:
                    name = f.read().strip()
                    # Verify the collection still exists
                    if self.collection_exists(name):
                        return name
                    else:
                        # Clean up stale reference
                        self.clear_current_collection()
            except Exception:
                pass
        return None
    
    def clear_current_collection(self) -> bool:
        """Clear the current collection."""
        try:
            if self.current_collection_file.exists():
                self.current_collection_file.unlink()
            return True
        except Exception as e:
            print(f"Error clearing current collection: {e}")
            return False
    
    def get_collection_templates(self, collection_name: str, storage: PromptStorage) -> List[PromptTemplate]:
        """Get all templates that belong to a collection."""
        collection = self.get_collection(collection_name)
        if not collection:
            return []
        
        templates = []
        for template_name in collection.templates:
            template = storage.get_prompt(template_name)
            if template:
                templates.append(template)
        
        return templates
    
    def validate_collection_templates(self, collection_name: str, storage: PromptStorage) -> Dict[str, List[str]]:
        """Validate that all templates in a collection exist."""
        collection = self.get_collection(collection_name)
        if not collection:
            return {"valid": [], "missing": []}
        
        valid = []
        missing = []
        
        for template_name in collection.templates:
            if storage.prompt_exists(template_name):
                valid.append(template_name)
            else:
                missing.append(template_name)
        
        return {"valid": valid, "missing": missing}


class CollectionManager:
    """High-level interface for collection operations."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize collection manager."""
        self.collection_storage = CollectionStorage(storage_path)
        self.prompt_storage = PromptStorage(storage_path)
    
    def create_collection(self, name: str, description: str = "", templates: List[str] = None, tags: List[str] = None) -> bool:
        """Create a new collection."""
        if self.collection_storage.collection_exists(name):
            return False
        
        from datetime import datetime
        
        collection = Collection(
            name=name,
            description=description,
            templates=templates or [],
            tags=tags or [],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        return self.collection_storage.save_collection(collection)
    
    def load_collection(self, name: str) -> bool:
        """Load a collection as the current working collection."""
        if self.collection_storage.collection_exists(name):
            return self.collection_storage.set_current_collection(name)
        return False
    
    def get_current_collection_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current collection."""
        current = self.collection_storage.get_current_collection()
        if not current:
            return None
        
        collection = self.collection_storage.get_collection(current)
        if not collection:
            return None
        
        validation = self.collection_storage.validate_collection_templates(current, self.prompt_storage)
        
        return {
            "collection": collection,
            "valid_templates": validation["valid"],
            "missing_templates": validation["missing"],
            "template_count": len(collection.templates)
        }
    
    def list_current_collection_templates(self) -> List[PromptTemplate]:
        """List templates in the current collection."""
        current = self.collection_storage.get_current_collection()
        if not current:
            return []
        
        return self.collection_storage.get_collection_templates(current, self.prompt_storage)
    
    def add_template_to_current_collection(self, template_name: str) -> bool:
        """Add a template to the current collection."""
        current = self.collection_storage.get_current_collection()
        if not current:
            return False
        
        if not self.prompt_storage.prompt_exists(template_name):
            return False
        
        collection = self.collection_storage.get_collection(current)
        if not collection:
            return False
        
        if collection.add_template(template_name):
            from datetime import datetime
            collection.updated_at = datetime.now().isoformat()
            return self.collection_storage.save_collection(collection)
        
        return False
    
    def remove_template_from_current_collection(self, template_name: str) -> bool:
        """Remove a template from the current collection."""
        current = self.collection_storage.get_current_collection()
        if not current:
            return False
        
        collection = self.collection_storage.get_collection(current)
        if not collection:
            return False
        
        if collection.remove_template(template_name):
            from datetime import datetime
            collection.updated_at = datetime.now().isoformat()
            return self.collection_storage.save_collection(collection)
        
        return False