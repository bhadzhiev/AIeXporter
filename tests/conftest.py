import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def temp_storage_dir():
    """Create a temporary storage directory for prompt tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage_dir = Path(tmp_dir) / ".prompts"
        storage_dir.mkdir(exist_ok=True)
        yield storage_dir


@pytest.fixture
def sample_template():
    """Sample template for testing."""
    return {
        "name": "test-prompt",
        "template": "Hello {name}, this is a test. Your favorite color is {color}.",
        "description": "A test prompt",
        "tags": ["test", "sample"],
    }


@pytest.fixture
def complex_template():
    """Complex template with commands for testing."""
    return {
        "name": "complex-prompt",
        "template": "System info: $(hostname), user: $(whoami), path: {path}",
        "description": "A prompt with commands",
        "tags": ["system", "info"],
    }