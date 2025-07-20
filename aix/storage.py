import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from .template import PromptTemplate


class PromptStorage:
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


    def _get_xml_template_path(self, name: str, collection: str = None) -> Path:
        """Get the file path for an XML template."""
        if collection:
            # Store in collection directory
            collection_dir = self.storage_path / "collections" / collection
            return collection_dir / f"{name}.xml"
        else:
            # Store in main directory
            return self.storage_path / f"{name}.xml"

    def save_prompt(self, prompt: PromptTemplate, collection: str = None) -> bool:
        """Save a prompt template as XML (default format)."""
        return self.save_prompt_xml(prompt, collection)

    def save_prompt_xml(self, prompt: PromptTemplate, collection: str = None) -> bool:
        """Save a prompt template as a single XML file."""
        try:
            # Create collection directory if needed
            if collection:
                collection_dir = self.storage_path / "collections" / collection
                collection_dir.mkdir(parents=True, exist_ok=True)

            # Save as single XML file
            xml_path = self._get_xml_template_path(prompt.name, collection)
            xml_content = prompt.to_xml()
            
            with open(xml_path, "w", encoding="utf-8") as f:
                f.write(xml_content)

            return True
        except Exception as e:
            print(f"Error saving XML prompt: {e}")
            return False

    def get_prompt(self, name: str, collection: str = None) -> Optional[PromptTemplate]:
        """Load a prompt template from storage (XML format only)."""
        # If collection is specified, try that first
        if collection:
            prompt = self._get_prompt_xml_from_location(name, collection)
            if prompt:
                return prompt
        
        # Try main directory (legacy location)
        prompt = self._get_prompt_xml_from_location(name, None)
        if prompt:
            return prompt
            
        # If not found and no collection specified, search all collections
        if not collection:
            collections_path = self.storage_path / "collections"
            if collections_path.exists():
                for collection_dir in collections_path.glob("*"):
                    if collection_dir.is_dir():
                        prompt = self._get_prompt_xml_from_location(name, collection_dir.name)
                        if prompt:
                            return prompt
        
        return None

    def _get_prompt_xml_from_location(self, name: str, collection: str = None) -> Optional[PromptTemplate]:
        """Load a prompt template from XML file."""
        xml_path = self._get_xml_template_path(name, collection)
        if xml_path.exists():
            try:
                with open(xml_path, "r", encoding="utf-8") as f:
                    xml_content = f.read()
                return PromptTemplate.from_xml(xml_content)
            except Exception as e:
                print(f"Error loading XML prompt {name}: {e}")
        return None


    def list_prompts(self) -> List[PromptTemplate]:
        """List all available prompt templates from XML files."""
        prompts = []
        seen_names = set()

        # Check main directory for XML files
        for file_path in self.storage_path.glob("*.xml"):
            name = file_path.stem
            if name in seen_names:
                continue
            seen_names.add(name)

            prompt = self.get_prompt(name)
            if prompt:
                prompts.append(prompt)

        # Check collections directories for XML files
        collections_path = self.storage_path / "collections"
        if collections_path.exists():
            for collection_dir in collections_path.glob("*"):
                if collection_dir.is_dir():
                    for file_path in collection_dir.glob("*.xml"):
                        name = file_path.stem
                        if name in seen_names:
                            continue
                        seen_names.add(name)

                        prompt = self.get_prompt(name, collection_dir.name)
                        if prompt:
                            prompts.append(prompt)

        return sorted(prompts, key=lambda p: p.name)

    def delete_prompt(self, name: str, collection: str = None) -> bool:
        """Delete a prompt template from storage (XML format)."""
        xml_path = self._get_xml_template_path(name, collection)
        
        if xml_path.exists():
            try:
                xml_path.unlink()
                return True
            except Exception as e:
                print(f"Error deleting {xml_path}: {e}")
                return False
        
        # If not found in specified collection, search all collections
        if not collection:
            collections_path = self.storage_path / "collections"
            if collections_path.exists():
                for collection_dir in collections_path.glob("*"):
                    if collection_dir.is_dir():
                        xml_path = self._get_xml_template_path(name, collection_dir.name)
                        if xml_path.exists():
                            try:
                                xml_path.unlink()
                                return True
                            except Exception as e:
                                print(f"Error deleting {xml_path}: {e}")
        
        return False

    def prompt_exists(self, name: str, collection: str = None) -> bool:
        """Check if a prompt with given name exists."""
        xml_path = self._get_xml_template_path(name, collection)
        if xml_path.exists():
            return True
            
        # If not found and no collection specified, search all collections
        if not collection:
            collections_path = self.storage_path / "collections"
            if collections_path.exists():
                for collection_dir in collections_path.glob("*"):
                    if collection_dir.is_dir():
                        xml_path = self._get_xml_template_path(name, collection_dir.name)
                        if xml_path.exists():
                            return True
        return False

    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about the storage location and contents."""
        prompts = self.list_prompts()
        
        # Calculate total size including all XML files
        total_size = 0
        xml_count = 0
        
        # Main directory XML files
        for f in self.storage_path.glob("*.xml"):
            total_size += f.stat().st_size
            xml_count += 1
            
        # Collections directory XML files
        collections_path = self.storage_path / "collections"
        if collections_path.exists():
            for collection_dir in collections_path.glob("*"):
                if collection_dir.is_dir():
                    for f in collection_dir.glob("*.xml"):
                        total_size += f.stat().st_size
                        xml_count += 1

        return {
            "storage_path": str(self.storage_path),
            "total_prompts": len(prompts),
            "total_size_bytes": total_size,
            "formats": {
                "xml": xml_count,
            },
        }
