import pytest
import json
from aix.api_client import (
    OpenRouterClient, 
    OpenAIClient, 
    AnthropicClient,
    APIResponse
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
            provider="test-provider"
        )
        
        assert response.content == "Test response content"
        assert response.model == "test-model"
        assert response.usage == {"prompt_tokens": 10, "completion_tokens": 20}
        assert response.cost == 0.001
        assert response.provider == "test-provider"
        assert response.raw_response is None

    def test_api_response_minimal(self):
        """Test API response with minimal fields."""
        response = APIResponse(
            content="Minimal response",
            model="minimal-model"
        )
        
        assert response.content == "Minimal response"
        assert response.model == "minimal-model"
        assert response.usage is None
        assert response.cost is None
        assert response.provider is None