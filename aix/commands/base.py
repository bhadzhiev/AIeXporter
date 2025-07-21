from abc import ABC, abstractmethod
from typing import Tuple


class Command(ABC):
    """Base Command interface for the Command pattern."""
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Tuple[bool, str, str]:
        """Execute the command and return (success, stdout, stderr)."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the command name."""
        pass
    
    def validate(self) -> bool:
        """Validate command parameters."""
        return True
    
    def get_description(self) -> str:
        """Return command description."""
        return ""


class SecurityValidator(ABC):
    """Interface for security validation."""
    
    @abstractmethod
    def is_allowed(self, command: str) -> bool:
        """Check if command is allowed."""
        pass
    
    @abstractmethod
    def get_error_message(self, command: str) -> str:
        """Get error message for disallowed command."""
        pass