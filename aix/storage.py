import json
import yaml
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
            env_path = os.environ.get('AIX_STORAGE_PATH')
            if env_path:
                self.storage_path = Path(env_path)
            else:
                self.storage_path = Path.home() / ".prompts"
        self.storage_path.mkdir(exist_ok=True)
    
    def _get_prompt_path(self, name: str, format: str = "yaml") -> Path:
        """Get the file path for a prompt metadata."""
        extension = "yaml" if format == "yaml" else "json"
        return self.storage_path / f"{name}.{extension}"
    
    def _get_template_path(self, name: str) -> Path:
        """Get the file path for a prompt template content."""
        return self.storage_path / f"{name}.txt"
    
    def save_prompt(self, prompt: PromptTemplate, format: str = "yaml") -> bool:
        """Save a prompt template to storage using separated files."""
        try:
            # Save template content to .txt file
            template_path = self._get_template_path(prompt.name)
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(prompt.template)
            
            # Save metadata without template content
            metadata_path = self._get_prompt_path(prompt.name, format)
            metadata = prompt.to_dict()
            # Remove template content from metadata, store reference instead
            metadata.pop('template', None)
            metadata['template_file'] = f"{prompt.name}.txt"
            
            if format == "yaml":
                with open(metadata_path, 'w') as f:
                    yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
            else:  # json
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving prompt: {e}")
            return False
    
    def get_prompt(self, name: str) -> Optional[PromptTemplate]:
        """Load a prompt template from storage using separated files."""
        # Try YAML first, then JSON for metadata
        for format in ["yaml", "json"]:
            metadata_path = self._get_prompt_path(name, format)
            if metadata_path.exists():
                try:
                    # Load metadata
                    if format == "yaml":
                        with open(metadata_path, 'r') as f:
                            metadata = yaml.safe_load(f)
                    else:  # json
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                    
                    # Load template content from .txt file
                    template_path = self._get_template_path(name)
                    if template_path.exists():
                        with open(template_path, 'r', encoding='utf-8') as f:
                            template_content = f.read()
                    else:
                        # Fallback: check if template is in metadata (old format)
                        template_content = metadata.get('template', '')
                    
                    # Combine metadata and template content
                    metadata['template'] = template_content
                    # Remove template_file reference as it's internal
                    metadata.pop('template_file', None)
                    
                    return PromptTemplate.from_dict(metadata)
                except Exception as e:
                    print(f"Error loading prompt {name}: {e}")
                    continue
        
        return None
    
    def list_prompts(self) -> List[PromptTemplate]:
        """List all available prompt templates."""
        prompts = []
        seen_names = set()
        
        for file_path in self.storage_path.glob("*"):
            if file_path.suffix in [".yaml", ".yml", ".json"]:
                name = file_path.stem
                # Skip config files
                if name in ["config", "settings"] or name in seen_names:
                    continue
                seen_names.add(name)
                
                prompt = self.get_prompt(name)
                if prompt:
                    prompts.append(prompt)
        
        return sorted(prompts, key=lambda p: p.name)
    
    def delete_prompt(self, name: str) -> bool:
        """Delete a prompt template from storage (both metadata and content files)."""
        deleted = False
        
        # Delete metadata files
        for format in ["yaml", "json"]:
            metadata_path = self._get_prompt_path(name, format)
            if metadata_path.exists():
                try:
                    metadata_path.unlink()
                    deleted = True
                except Exception as e:
                    print(f"Error deleting {metadata_path}: {e}")
        
        # Delete template content file
        template_path = self._get_template_path(name)
        if template_path.exists():
            try:
                template_path.unlink()
                deleted = True
            except Exception as e:
                print(f"Error deleting {template_path}: {e}")
        
        return deleted
    
    def prompt_exists(self, name: str) -> bool:
        """Check if a prompt with given name exists."""
        for format in ["yaml", "json"]:
            if self._get_prompt_path(name, format).exists():
                return True
        return False
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about the storage location and contents."""
        prompts = self.list_prompts()
        total_size = sum(f.stat().st_size for f in self.storage_path.iterdir() if f.is_file())
        
        return {
            "storage_path": str(self.storage_path),
            "total_prompts": len(prompts),
            "total_size_bytes": total_size,
            "formats": {
                "yaml": len(list(self.storage_path.glob("*.yaml"))) + len(list(self.storage_path.glob("*.yml"))),
                "json": len(list(self.storage_path.glob("*.json")))
            }
        }