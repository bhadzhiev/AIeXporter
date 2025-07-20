"""Collection management for organizing prompt templates."""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from .template import PromptTemplate
from .storage import PromptStorage


@dataclass
class Collection:
    """Represents a collection of prompt templates."""

    name: str
    description: str = ""
    templates: List[str] = None  # List of template names
    system_prompt: Optional[str] = None  # JSON string for system prompt
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
    def from_dict(cls, data: Dict[str, Any]) -> "Collection":
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
            env_path = os.environ.get("AIX_STORAGE_PATH")
            if env_path:
                self.storage_path = Path(env_path)
            else:
                self.storage_path = Path.home() / ".prompts"
        self.collections_path = self.storage_path / "collections"
        self.collections_path.mkdir(parents=True, exist_ok=True)

        # File to track the currently loaded collection
        self.current_collection_file = self.storage_path / ".current_collection"

    
    def save_collection(self, collection: Collection) -> bool:
        """Save a collection to XML format."""
        return self.save_collection_to_xml(collection)

    def save_collection_to_xml(self, collection: Collection) -> bool:
        """Save a collection to a single XML file with embedded templates."""
        try:
            xml_path = self.collections_path / f"{collection.name}.xml"
            
            # Create root element
            root = ET.Element("collection")
            
            # Add metadata
            metadata = ET.SubElement(root, "metadata")
            ET.SubElement(metadata, "name").text = collection.name
            ET.SubElement(metadata, "description").text = collection.description or ""
            
            if collection.system_prompt:
                ET.SubElement(metadata, "system_prompt").text = collection.system_prompt
            
            # Add tags
            if collection.tags:
                tags_elem = ET.SubElement(metadata, "tags")
                for tag in collection.tags:
                    ET.SubElement(tags_elem, "tag").text = tag
            
            ET.SubElement(metadata, "author").text = collection.author or ""
            ET.SubElement(metadata, "created_at").text = collection.created_at
            ET.SubElement(metadata, "updated_at").text = collection.updated_at
            
            # Add templates section
            templates_elem = ET.SubElement(root, "templates")
            
            # Load and embed each template
            template_idx = 0
            for template_name in collection.templates:
                template = self._load_template_for_collection(template_name)
                if template:
                    template_elem = ET.SubElement(templates_elem, "template")
                    
                    # Template metadata
                    tmpl_metadata = ET.SubElement(template_elem, "metadata")
                    ET.SubElement(tmpl_metadata, "name").text = template.name
                    ET.SubElement(tmpl_metadata, "description").text = template.description or ""
                    ET.SubElement(tmpl_metadata, "created_at").text = template.created_at
                    ET.SubElement(tmpl_metadata, "updated_at").text = template.updated_at
                    
                    # Placeholder generators
                    if template.placeholder_generators:
                        generators_elem = ET.SubElement(tmpl_metadata, "placeholder_generators")
                        for gen_idx, generator in enumerate(template.placeholder_generators):
                            gen_elem = ET.SubElement(generators_elem, "placeholder_generator")
                            gen_elem.set("language", generator.language)
                            gen_elem.text = f"PLACEHOLDER_GENERATOR_CDATA_{generator.language}_{template_idx}_{gen_idx}"
                    
                    # Template content with CDATA
                    content_elem = ET.SubElement(template_elem, "content")
                    content_elem.text = "PLACEHOLDER_FOR_CDATA"
                    
                    template_idx += 1
            
            # Convert to string and replace placeholders with CDATA
            xml_string = ET.tostring(root, encoding="unicode")
            
            # Add XML declaration
            xml_string = '<?xml version="1.0" encoding="utf-8"?>\n' + xml_string
            
            # Replace content placeholders with CDATA
            template_idx = 0
            for template_name in collection.templates:
                template = self._load_template_for_collection(template_name)
                if template:
                    # Replace template content
                    cdata_content = f"<![CDATA[{template.template}]]>"
                    xml_string = xml_string.replace("PLACEHOLDER_FOR_CDATA", cdata_content, 1)
                    
                    # Replace placeholder generator CDATA sections
                    if template.placeholder_generators:
                        for gen_idx, generator in enumerate(template.placeholder_generators):
                            placeholder = f"PLACEHOLDER_GENERATOR_CDATA_{generator.language}_{template_idx}_{gen_idx}"
                            cdata_script = f"<![CDATA[{generator.script}]]>"
                            xml_string = xml_string.replace(placeholder, cdata_script)
                    
                    template_idx += 1
            
            # Write to file
            with open(xml_path, "w", encoding="utf-8") as f:
                f.write(xml_string)
            
            return True
        except Exception as e:
            print(f"Error saving collection to XML: {e}")
            return False

    def _load_template_for_collection(self, template_name: str) -> Optional[PromptTemplate]:
        """Load a template from storage for embedding in collection."""
        # First try to load from prompt storage
        storage = PromptStorage(self.storage_path)
        template = storage.get_prompt(template_name)
        if template:
            return template
        
        # If not found, try to load from any collection directory
        for collection_dir in self.collections_path.glob("*"):
            if collection_dir.is_dir():
                template_path = collection_dir / f"{template_name}.xml"
                if template_path.exists():
                    return storage.get_prompt(template_name, collection_dir.name)
        
        return None

    def get_collection(self, name: str) -> Optional[Collection]:
        """Load a collection from XML format."""
        # First try XML format
        xml_collection = self.get_collection_from_xml(name)
        if xml_collection:
            # For backward compatibility, also check directory for additional templates
            collection_dir = self.collections_path / name
            if collection_dir.exists() and collection_dir.is_dir():
                # Auto-discover templates in directory and validate against actual files
                discovered_templates = []
                for xml_file in collection_dir.glob("*.xml"):
                    template_name = xml_file.stem
                    discovered_templates.append(template_name)
                
                # Use discovered templates as the authoritative list for directory-based collections
                # This ensures consistency with actual file system state
                all_templates = discovered_templates
                if all_templates != xml_collection.templates:
                    xml_collection.templates = all_templates
                    xml_collection.updated_at = __import__('datetime').datetime.now().isoformat()
                    self.save_collection(xml_collection)
            
            return xml_collection
            
        # For backward compatibility, check for directory-based collection
        collection_dir = self.collections_path / name
        if collection_dir.exists() and collection_dir.is_dir():
            # Auto-discover templates in directory
            templates = []
            for xml_file in collection_dir.glob("*.xml"):
                templates.append(xml_file.stem)
            
            if templates:
                # Create a collection with discovered templates
                from datetime import datetime
                collection = Collection(
                    name=name,
                    description="",
                    templates=templates,
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat(),
                )
                return collection
                
        return None

    def get_collection_from_xml(self, name: str) -> Optional[Collection]:
        """Load a collection from an XML file."""
        xml_path = self.collections_path / f"{name}.xml"
        if not xml_path.exists():
            return None
        
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            if root.tag != "collection":
                return None
            
            # Parse metadata
            metadata = root.find("metadata")
            if metadata is None:
                return None
            
            collection_data = {
                "name": metadata.findtext("name", name),
                "description": metadata.findtext("description", ""),
                "system_prompt": metadata.findtext("system_prompt"),
                "author": metadata.findtext("author", ""),
                "created_at": metadata.findtext("created_at", ""),
                "updated_at": metadata.findtext("updated_at", ""),
                "tags": [],
                "templates": []
            }
            
            # Parse tags
            tags_elem = metadata.find("tags")
            if tags_elem is not None:
                collection_data["tags"] = [tag.text for tag in tags_elem.findall("tag") if tag.text]
            
            # Parse template names from embedded templates
            templates_elem = root.find("templates")
            if templates_elem is not None:
                for template_elem in templates_elem.findall("template"):
                    template_metadata = template_elem.find("metadata")
                    if template_metadata is not None:
                        template_name = template_metadata.findtext("name")
                        if template_name:
                            collection_data["templates"].append(template_name)
            
            return Collection.from_dict(collection_data)
            
        except Exception as e:
            print(f"Error loading collection from XML {xml_path}: {e}")
            return None

    def list_collections(self) -> List[Collection]:
        """List all available collections from XML format."""
        collections = []

        # Scan for XML-based collections only
        for xml_path in self.collections_path.glob("*.xml"):
            name = xml_path.stem
            collection = self.get_collection_from_xml(name)
            if collection:
                collections.append(collection)

        return sorted(collections, key=lambda c: c.name)

    def delete_collection(self, name: str) -> bool:
        """Delete a collection from XML storage."""
        # Delete XML collection
        xml_path = self.collections_path / f"{name}.xml"
        if xml_path.exists():
            try:
                xml_path.unlink()
                # Clear current collection if it was the deleted one
                if self.get_current_collection() == name:
                    self.clear_current_collection()
                return True
            except Exception as e:
                print(f"Error deleting XML collection {xml_path}: {e}")
                return False
        else:
            return False

    def collection_exists(self, name: str) -> bool:
        """Check if a collection exists in XML format."""
        xml_path = self.collections_path / f"{name}.xml"
        return xml_path.exists()

    def set_current_collection(self, name: str) -> bool:
        """Set the current active collection."""
        if self.collection_exists(name):
            try:
                with open(self.current_collection_file, "w") as f:
                    f.write(name)
                return True
            except Exception as e:
                print(f"Error setting current collection: {e}")
        return False

    def get_current_collection(self) -> Optional[str]:
        """Get the name of the current active collection."""
        if self.current_collection_file.exists():
            try:
                with open(self.current_collection_file, "r") as f:
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

    def get_xml_collection_template(self, collection_name: str, template_name: str) -> Optional[PromptTemplate]:
        """Get a specific template from an XML collection."""
        xml_path = self.collections_path / f"{collection_name}.xml"
        if not xml_path.exists():
            return None
        
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Find the template in the XML
            templates_elem = root.find("templates")
            if templates_elem is not None:
                for template_elem in templates_elem.findall("template"):
                    template_metadata = template_elem.find("metadata")
                    if template_metadata is not None:
                        name = template_metadata.findtext("name")
                        if name == template_name:
                            # Parse template data
                            template_data = {
                                "name": name,
                                "description": template_metadata.findtext("description", ""),
                                "created_at": template_metadata.findtext("created_at", ""),
                                "updated_at": template_metadata.findtext("updated_at", ""),
                                "template": "",
                                "placeholder_generators": []
                            }
                            
                            # Parse placeholder generators
                            generators_elem = template_metadata.find("placeholder_generators")
                            if generators_elem is not None:
                                for gen_elem in generators_elem.findall("placeholder_generator"):
                                    language = gen_elem.get("language", "")
                                    script = gen_elem.text or ""
                                    if language and script:
                                        template_data["placeholder_generators"].append({
                                            "language": language,
                                            "script": script
                                        })
                            
                            # Get content (handle CDATA)
                            content_elem = template_elem.find("content")
                            if content_elem is not None and content_elem.text:
                                template_data["template"] = content_elem.text
                            
                            return PromptTemplate.from_dict(template_data)
            
            return None
            
        except Exception as e:
            print(f"Error loading template {template_name} from XML collection {collection_name}: {e}")
            return None

    def get_collection_templates(
        self, collection_name: str, storage: PromptStorage
    ) -> List[PromptTemplate]:
        """Get all templates that belong to a collection."""
        collection = self.get_collection(collection_name)
        if not collection:
            return []

        templates = []
        
        # Check if this is an XML collection first
        xml_path = self.collections_path / f"{collection_name}.xml"
        if xml_path.exists():
            # Load templates directly from XML
            for template_name in collection.templates:
                template = self.get_xml_collection_template(collection_name, template_name)
                if template:
                    templates.append(template)
        else:
            # Use directory-based approach - scan collection directory for XML files
            collection_dir = self.collections_path / collection_name
            if collection_dir.exists() and collection_dir.is_dir():
                for xml_file in collection_dir.glob("*.xml"):
                    template_name = xml_file.stem
                    template = storage.get_prompt(template_name, collection_name)
                    if template:
                        templates.append(template)
            else:
                # Fallback to templates list in collection
                for template_name in collection.templates:
                    template = storage.get_prompt(template_name)
                    if template:
                        templates.append(template)

        return templates

    def validate_collection_templates(
        self, collection_name: str, storage: PromptStorage
    ) -> Dict[str, List[str]]:
        """Validate that all templates in a collection exist."""
        collection = self.get_collection(collection_name)
        if not collection:
            return {"valid": [], "missing": []}

        valid = []
        missing = []

        # For directory-based collections, auto-discover templates
        xml_path = self.collections_path / f"{collection_name}.xml"
        if not xml_path.exists():
            collection_dir = self.collections_path / collection_name
            if collection_dir.exists() and collection_dir.is_dir():
                # Auto-discover templates in directory
                discovered_templates = []
                for xml_file in collection_dir.glob("*.xml"):
                    template_name = xml_file.stem
                    discovered_templates.append(template_name)
                
                # Update collection with discovered templates
                if discovered_templates:
                    collection.templates = discovered_templates
                    collection.updated_at = __import__('datetime').datetime.now().isoformat()
                    self.save_collection(collection)

        for template_name in collection.templates:
            if storage.prompt_exists(template_name, collection_name):
                valid.append(template_name)
            elif storage.prompt_exists(template_name):
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

    def create_collection(
        self,
        name: str,
        description: str = "",
        templates: List[str] = None,
        tags: List[str] = None,
        system_prompt: str = None,
    ) -> bool:
        """Create a new collection."""
        if self.collection_storage.collection_exists(name):
            return False

        from datetime import datetime

        collection = Collection(
            name=name,
            description=description,
            templates=templates or [],
            system_prompt=system_prompt,
            tags=tags or [],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
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

        validation = self.collection_storage.validate_collection_templates(
            current, self.prompt_storage
        )

        return {
            "collection": collection,
            "valid_templates": validation["valid"],
            "missing_templates": validation["missing"],
            "template_count": len(collection.templates),
        }

    def list_current_collection_templates(self) -> List[PromptTemplate]:
        """List templates in the current collection."""
        current = self.collection_storage.get_current_collection()
        if not current:
            return []

        return self.collection_storage.get_collection_templates(
            current, self.prompt_storage
        )

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

    def export_collection(
        self,
        collection_name: str,
        export_path: Path,
        include_templates: bool = True,
    ) -> bool:
        """Export a collection as a bundle (tar.gz with XML and templates)."""
        import tarfile
        import tempfile
        import json
        import shutil
        from datetime import datetime

        # Check if collection exists
        collection = self.collection_storage.get_collection(collection_name)
        if not collection:
            return False

        export_path = Path(export_path)
        export_path.mkdir(parents=True, exist_ok=True)
        
        # Create bundle file name
        bundle_file = export_path / f"{collection_name}-bundle.tar.gz"
        
        try:
            with tarfile.open(bundle_file, "w:gz") as tar:
                # Add collection XML file
                xml_path = self.collection_storage.collections_path / f"{collection_name}.xml"
                if xml_path.exists():
                    tar.add(xml_path, arcname=f"{collection_name}.xml")
                
                # Create manifest
                manifest = {
                    "collection_name": collection_name,
                    "exported_at": datetime.now().isoformat(),
                    "version": "1.0",
                    "include_templates": include_templates,
                    "templates": collection.templates,
                }
                
                # Add manifest as JSON
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump(manifest, f, indent=2)
                    manifest_path = Path(f.name)
                
                tar.add(manifest_path, arcname="manifest.json")
                manifest_path.unlink()
                
                # Include template files if requested
                if include_templates:
                    for template_name in collection.templates:
                        template = self.prompt_storage.get_prompt(template_name)
                        if template:
                            # Add template metadata (YAML/JSON)
                            metadata_path = self.prompt_storage.storage_path / f"{template_name}.yaml"
                            if metadata_path.exists():
                                tar.add(metadata_path, arcname=f"templates/{template_name}.yaml")
                            else:
                                # Try JSON format
                                metadata_path = self.prompt_storage.storage_path / f"{template_name}.json"
                                if metadata_path.exists():
                                    tar.add(metadata_path, arcname=f"templates/{template_name}.json")
                            
                            # Add template content
                            content_path = self.prompt_storage.storage_path / f"{template_name}.txt"
                            if content_path.exists():
                                tar.add(content_path, arcname=f"templates/{template_name}.txt")
            
            return True
        except Exception as e:
            print(f"Error exporting collection: {e}")
            return False

    def import_collection(
        self, import_path: Path, overwrite: bool = False
    ) -> Dict[str, Any]:
        """Import a collection from a bundle file."""
        import tarfile
        import json
        import tempfile
        import shutil

        import_path = Path(import_path)
        result = {
            "success": False,
            "collection_name": None,
            "imported_templates": [],
            "skipped_templates": [],
            "errors": [],
        }

        try:
            if import_path.suffix == ".gz" and import_path.name.endswith(".tar.gz"):
                # Handle bundle import
                with tarfile.open(import_path, "r:gz") as tar:
                    # Extract to temporary directory
                    with tempfile.TemporaryDirectory() as temp_dir:
                        temp_path = Path(temp_dir)
                        tar.extractall(temp_path, filter='data')  # Use filter for security
                        
                        # Read manifest
                        manifest_path = temp_path / "manifest.json"
                        if not manifest_path.exists():
                            result["errors"].append("Invalid bundle: missing manifest")
                            return result
                        
                        with open(manifest_path) as f:
                            manifest = json.load(f)
                        
                        collection_name = manifest["collection_name"]
                        result["collection_name"] = collection_name
                        
                        # Check if collection exists
                        if self.collection_storage.collection_exists(collection_name) and not overwrite:
                            result["errors"].append(
                                f"Collection '{collection_name}' already exists (use --overwrite)"
                            )
                            return result
                        
                        # Import collection XML
                        xml_path = temp_path / f"{collection_name}.xml"
                        if xml_path.exists():
                            dest_xml_path = self.collection_storage.collections_path / f"{collection_name}.xml"
                            shutil.copy2(xml_path, dest_xml_path)
                        
                        # Import templates if they exist in bundle
                        templates_dir = temp_path / "templates"
                        if templates_dir.exists():
                            for template_file in templates_dir.glob("*.yaml"):
                                template_name = template_file.stem
                                
                                # Skip if template already exists and not overwriting
                                if self.prompt_storage.prompt_exists(template_name) and not overwrite:
                                    result["skipped_templates"].append(template_name)
                                    continue
                                
                                # Import template metadata
                                dest_metadata_path = self.prompt_storage.storage_path / f"{template_name}.yaml"
                                shutil.copy2(template_file, dest_metadata_path)
                                
                                # Import template content
                                content_file = templates_dir / f"{template_name}.txt"
                                if content_file.exists():
                                    dest_content_path = self.prompt_storage.storage_path / f"{template_name}.txt"
                                    shutil.copy2(content_file, dest_content_path)
                                
                                result["imported_templates"].append(template_name)
                            
                            # Also check for JSON files
                            for template_file in templates_dir.glob("*.json"):
                                template_name = template_file.stem
                                
                                # Skip if template already exists and not overwriting
                                if self.prompt_storage.prompt_exists(template_name) and not overwrite:
                                    result["skipped_templates"].append(template_name)
                                    continue
                                
                                # Import template metadata
                                dest_metadata_path = self.prompt_storage.storage_path / f"{template_name}.json"
                                shutil.copy2(template_file, dest_metadata_path)
                                
                                # Import template content
                                content_file = templates_dir / f"{template_name}.txt"
                                if content_file.exists():
                                    dest_content_path = self.prompt_storage.storage_path / f"{template_name}.txt"
                                    shutil.copy2(content_file, dest_content_path)
                                
                                result["imported_templates"].append(template_name)
                        
                        result["success"] = True
                        
            elif import_path.suffix == ".xml":
                # Handle legacy XML import
                collection_name = import_path.stem
                result["collection_name"] = collection_name

                # Check if collection exists
                if self.collection_storage.collection_exists(collection_name) and not overwrite:
                    result["errors"].append(
                        f"Collection '{collection_name}' already exists (use --overwrite)"
                    )
                    return result

                # Copy XML file to collections directory
                dest_path = self.collection_storage.collections_path / f"{collection_name}.xml"
                shutil.copy2(import_path, dest_path)
                
                # Load collection to get template names for result
                collection = self.collection_storage.get_collection(collection_name)
                if collection:
                    result["imported_templates"] = collection.templates
                    result["success"] = True
                else:
                    result["errors"].append("Failed to load imported collection")
            else:
                result["errors"].append("Only .tar.gz bundles and .xml files are supported for import")

        except Exception as e:
            result["errors"].append(f"Import failed: {e}")

        return result


