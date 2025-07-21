import pytest
from aix.api_client import (
    OpenRouterClient,
    OpenAIClient,
    AnthropicClient,
    CustomAPIClient,
    APIResponse,
    get_client,
)


class TestOpenRouterClient:
    """Test OpenRouter client functionality."""

    def test_client_initialization(self):
        """Test client initialization."""
        client = OpenRouterClient("test-key")

        assert client.api_key == "test-key"
        assert client.base_url == "https://openrouter.ai/api/v1"

    def test_close_client(self):
        """Test client cleanup."""
        client = OpenRouterClient("test-key")
        client.close()
        # Should not raise any exceptions


class TestOpenAIClient:
    """Test OpenAI client functionality."""

    def test_client_initialization(self):
        """Test client initialization."""
        client = OpenAIClient("test-key")

        assert client.api_key == "test-key"
        assert client.base_url == "https://api.openai.com/v1"

    def test_close_client(self):
        """Test client cleanup."""
        client = OpenAIClient("test-key")
        client.close()
        # Should not raise any exceptions


class TestAnthropicClient:
    """Test Anthropic client functionality."""

    def test_client_initialization(self):
        """Test client initialization."""
        client = AnthropicClient("test-key")

        assert client.api_key == "test-key"
        assert client.base_url == "https://api.anthropic.com/v1"

    def test_close_client(self):
        """Test client cleanup."""
        client = AnthropicClient("test-key")
        client.close()
        # Should not raise any exceptions


class TestAPIResponse:
    """Test API response structure."""

    def test_api_response_creation(self):
        """Test API response creation."""
        response = APIResponse(
            content="Test response content",
            model="test-model",
            usage={"prompt_tokens": 10, "completion_tokens": 20},
            cost=0.001,
            provider="test-provider",
        )

        assert response.content == "Test response content"
        assert response.model == "test-model"
        assert response.usage == {"prompt_tokens": 10, "completion_tokens": 20}
        assert response.cost == 0.001
        assert response.provider == "test-provider"
        assert response.raw_response is None

    def test_api_response_minimal(self):
        """Test API response with minimal fields."""
        response = APIResponse(content="Minimal response", model="minimal-model")

        assert response.content == "Minimal response"
        assert response.model == "minimal-model"
        assert response.usage is None
        assert response.cost is None
        assert response.provider is None


class TestCustomAPIClient:
    """Test Custom API client functionality."""

    def test_client_initialization(self):
        """Test custom client initialization."""
        headers = {"X-Custom-Header": "test-value"}
        client = CustomAPIClient(
            "test-key",
            "http://localhost:11434/v1",
            headers=headers,
            provider_name="ollama",
        )

        assert client.api_key == "test-key"
        assert client.base_url == "http://localhost:11434/v1"
        assert client.custom_headers == headers
        assert client.provider_name == "ollama"

    def test_client_initialization_minimal(self):
        """Test custom client initialization with minimal config."""
        client = CustomAPIClient("test-key", "http://localhost:8080/v1")

        assert client.api_key == "test-key"
        assert client.base_url == "http://localhost:8080/v1"
        assert client.custom_headers == {}
        assert client.provider_name == "custom"

    def test_close_client(self):
        """Test client cleanup."""
        client = CustomAPIClient("test-key", "http://localhost:8080/v1")
        client.close()
        # Should not raise any exceptions


class TestGetClient:
    """Test get_client factory function."""

    def test_get_openrouter_client(self):
        """Test getting OpenRouter client."""
        client = get_client("openrouter", "test-key")
        assert isinstance(client, OpenAIClient)
        assert client.api_key == "test-key"
        assert "openrouter.ai" in client.base_url

    def test_get_openai_client(self):
        """Test getting OpenAI client."""
        client = get_client("openai", "test-key")
        assert isinstance(client, OpenAIClient)
        assert client.api_key == "test-key"
        assert "api.openai.com" in client.base_url

    def test_get_anthropic_client(self):
        """Test getting Anthropic client."""
        client = get_client("anthropic", "test-key")
        assert isinstance(client, AnthropicClient)
        assert client.api_key == "test-key"
        assert "api.anthropic.com" in client.base_url

    def test_get_custom_client(self):
        """Test getting custom client."""
        custom_config = {
            "base_url": "http://localhost:11434/v1",
            "headers": {"X-Custom": "test"},
            "name": "ollama",
        }
        client = get_client("custom", "test-key", custom_config)
        assert isinstance(client, CustomAPIClient)
        assert client.api_key == "test-key"
        assert client.base_url == "http://localhost:11434/v1"
        assert client.custom_headers == {"X-Custom": "test"}
        assert client.provider_name == "ollama"

    def test_get_custom_client_no_config(self):
        """Test getting custom client without config raises error."""
        with pytest.raises(ValueError, match="Unsupported provider: custom"):
            get_client("custom", "test-key")
    
    def test_get_custom_client_legacy_prefix(self):
        """Test backward compatibility with custom: prefix."""
        custom_config = {
            "base_url": "http://localhost:11434/v1",
            "headers": {"X-Custom": "test"},
            "name": "ollama",
            "auth_type": "bearer"
        }
        
        # Both should work the same
        client1 = get_client("custom:test", "test-key", custom_config)
        client2 = get_client("test", "test-key", custom_config)
        
        assert isinstance(client1, CustomAPIClient)
        assert isinstance(client2, CustomAPIClient)
        assert client1.base_url == client2.base_url
        assert client1.provider_name == client2.provider_name

    def test_get_unsupported_provider(self):
        """Test getting unsupported provider raises error."""
        with pytest.raises(ValueError, match="Unsupported provider: invalid"):
            get_client("invalid", "test-key")
