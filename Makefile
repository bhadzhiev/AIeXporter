.PHONY: test lint fmt type update clean

# Run tests
test:
	uv run pytest

# Lint code with ruff
lint:
	uv run ruff check .

# Format code with ruff  
fmt:
	uv run ruff format .

# Type check with mypy
type:
	uv run mypy aix

# Update dependencies
update:
	uv lock --upgrade && uv sync --group dev

# Clean build artifacts
clean:
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete