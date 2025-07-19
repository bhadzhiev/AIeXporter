"""Collection management for organizing prompt templates."""

import json
import yaml
import os
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
        if storage_path:
            self.storage_path = storage_path
        else:
            # Check environment variable first, then fall back to default
            env_path = os.environ.get('AIX_STORAGE_PATH')
            if env_path:
                self.storage_path = Path(env_path)
            else:
                self.storage_path = Path.home() / ".prompts"
        self.collections_path = self.storage_path / "collections"
        self.collections_path.mkdir(parents=True, exist_ok=True)
        
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
    
    def export_collection(self, collection_name: str, export_path: Path, include_templates: bool = True, format: str = "yaml") -> bool:
        """Export a collection and optionally its templates to a directory or file."""
        import shutil
        import tarfile
        from datetime import datetime
        
        collection = self.collection_storage.get_collection(collection_name)
        if not collection:
            return False
            
        export_path = Path(export_path)
        
        if include_templates:
            # Create bundle directory
            bundle_dir = export_path / f"{collection_name}-bundle"
            bundle_dir.mkdir(parents=True, exist_ok=True)
            
            # Export collection metadata
            collection_file = bundle_dir / f"collection.{format}"
            if format == "yaml":
                with open(collection_file, 'w') as f:
                    yaml.dump(collection.to_dict(), f, default_flow_style=False, sort_keys=False)
            else:  # json
                with open(collection_file, 'w') as f:
                    json.dump(collection.to_dict(), f, indent=2)
            
            # Export templates
            templates_dir = bundle_dir / "templates"
            templates_dir.mkdir(exist_ok=True)
            
            exported_templates = []
            missing_templates = []
            
            for template_name in collection.templates:
                template = self.prompt_storage.get_prompt(template_name)
                if template:
                    # Export template metadata
                    template_meta_file = templates_dir / f"{template_name}.{format}"
                    template_data = template.to_dict()
                    template_data.pop('template', None)  # Remove content, store separately
                    template_data['template_file'] = f"{template_name}.txt"
                    
                    if format == "yaml":
                        with open(template_meta_file, 'w') as f:
                            yaml.dump(template_data, f, default_flow_style=False, sort_keys=False)
                    else:  # json
                        with open(template_meta_file, 'w') as f:
                            json.dump(template_data, f, indent=2)
                    
                    # Export template content
                    template_content_file = templates_dir / f"{template_name}.txt"
                    with open(template_content_file, 'w', encoding='utf-8') as f:
                        f.write(template.template)
                    
                    exported_templates.append(template_name)
                else:
                    missing_templates.append(template_name)
            
            # Create manifest
            manifest = {
                "collection_name": collection_name,
                "exported_at": datetime.now().isoformat(),
                "format": format,
                "exported_templates": exported_templates,
                "missing_templates": missing_templates,
                "total_templates": len(collection.templates)
            }
            
            with open(bundle_dir / "manifest.json", 'w') as f:
                json.dump(manifest, f, indent=2)
            
            # Create tar.gz archive
            archive_path = export_path / f"{collection_name}-bundle.tar.gz"
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(bundle_dir, arcname=f"{collection_name}-bundle")
            
            # Clean up temporary directory
            shutil.rmtree(bundle_dir)
            
            return True
        else:
            # Export only collection metadata
            collection_file = export_path / f"{collection_name}.{format}"
            collection_file.parent.mkdir(parents=True, exist_ok=True)
            
            if format == "yaml":
                with open(collection_file, 'w') as f:
                    yaml.dump(collection.to_dict(), f, default_flow_style=False, sort_keys=False)
            else:  # json
                with open(collection_file, 'w') as f:
                    json.dump(collection.to_dict(), f, indent=2)
            
            return True
    
    def import_collection(self, import_path: Path, overwrite: bool = False) -> Dict[str, Any]:
        """Import a collection from a file or bundle."""
        import tarfile
        import tempfile
        import shutil
        from datetime import datetime
        
        import_path = Path(import_path)
        result = {
            "success": False,
            "collection_name": None,
            "imported_templates": [],
            "skipped_templates": [],
            "errors": []
        }
        
        try:
            if import_path.suffix == ".gz" and import_path.name.endswith(".tar.gz"):
                # Import from bundle
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    
                    # Extract bundle
                    with tarfile.open(import_path, "r:gz") as tar:
                        # Use data_filter for Python 3.12+ to avoid deprecation warning
                        if hasattr(tarfile, 'data_filter'):
                            tar.extractall(temp_path, filter=tarfile.data_filter)
                        else:
                            tar.extractall(temp_path)
                    
                    # Find bundle directory
                    bundle_dirs = [d for d in temp_path.iterdir() if d.is_dir()]
                    if not bundle_dirs:
                        result["errors"].append("No bundle directory found in archive")
                        return result
                    
                    bundle_dir = bundle_dirs[0]
                    
                    # Read manifest
                    manifest_file = bundle_dir / "manifest.json"
                    if manifest_file.exists():
                        with open(manifest_file, 'r') as f:
                            manifest = json.load(f)
                        result["collection_name"] = manifest["collection_name"]
                    
                    # Import collection
                    collection_files = list(bundle_dir.glob("collection.*"))
                    if not collection_files:
                        result["errors"].append("No collection file found in bundle")
                        return result
                    
                    collection_file = collection_files[0]
                    collection_data = self._load_collection_file(collection_file)
                    if not collection_data:
                        result["errors"].append("Failed to load collection metadata")
                        return result
                    
                    collection_name = collection_data["name"]
                    
                    # Check if collection exists
                    if self.collection_storage.collection_exists(collection_name) and not overwrite:
                        result["errors"].append(f"Collection '{collection_name}' already exists (use --overwrite)")
                        return result
                    
                    # Import templates
                    templates_dir = bundle_dir / "templates"
                    if templates_dir.exists():
                        for template_meta_file in templates_dir.glob("*.yaml") or templates_dir.glob("*.json"):
                            if template_meta_file.stem == "manifest":
                                continue
                                
                            template_name = template_meta_file.stem
                            
                            # Check if template exists
                            if self.prompt_storage.prompt_exists(template_name) and not overwrite:
                                result["skipped_templates"].append(template_name)
                                continue
                            
                            # Load template metadata
                            template_data = self._load_collection_file(template_meta_file)
                            if not template_data:
                                result["errors"].append(f"Failed to load template metadata: {template_name}")
                                continue
                            
                            # Load template content
                            template_content_file = templates_dir / f"{template_name}.txt"
                            if template_content_file.exists():
                                with open(template_content_file, 'r', encoding='utf-8') as f:
                                    template_content = f.read()
                                template_data['template'] = template_content
                            
                            # Create and save template
                            try:
                                template = PromptTemplate.from_dict(template_data)
                                if self.prompt_storage.save_prompt(template):
                                    result["imported_templates"].append(template_name)
                                else:
                                    result["errors"].append(f"Failed to save template: {template_name}")
                            except Exception as e:
                                result["errors"].append(f"Failed to create template {template_name}: {e}")
                    
                    # Save collection
                    collection_data["updated_at"] = datetime.now().isoformat()
                    collection = Collection.from_dict(collection_data)
                    if self.collection_storage.save_collection(collection):
                        result["success"] = True
                        result["collection_name"] = collection_name
                    else:
                        result["errors"].append("Failed to save collection")
            
            else:
                # Import collection metadata only
                collection_data = self._load_collection_file(import_path)
                if not collection_data:
                    result["errors"].append("Failed to load collection file")
                    return result
                
                collection_name = collection_data["name"]
                
                # Check if collection exists
                if self.collection_storage.collection_exists(collection_name) and not overwrite:
                    result["errors"].append(f"Collection '{collection_name}' already exists (use --overwrite)")
                    return result
                
                # Save collection
                collection_data["updated_at"] = datetime.now().isoformat()
                collection = Collection.from_dict(collection_data)
                if self.collection_storage.save_collection(collection):
                    result["success"] = True
                    result["collection_name"] = collection_name
                else:
                    result["errors"].append("Failed to save collection")
        
        except Exception as e:
            result["errors"].append(f"Import failed: {e}")
        
        return result
    
    def _load_collection_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Helper to load collection data from YAML or JSON file."""
        try:
            if file_path.suffix in ['.yaml', '.yml']:
                with open(file_path, 'r') as f:
                    return yaml.safe_load(f)
            elif file_path.suffix == '.json':
                with open(file_path, 'r') as f:
                    return json.load(f)
        except Exception:
            return None
        return None