import httpx
import json
from typing import Dict, Any, Optional, Generator
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class Provider(Enum):
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    TOGETHER = "together"
    CUSTOM = "custom"


@dataclass
class APIResponse:
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    cost: Optional[float] = None
    provider: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class BaseAPIClient(ABC):
    def __init__(self, api_key: str, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.Client(timeout=60.0)

    @abstractmethod
    def generate(self, prompt: str, model: str = None, **kwargs) -> APIResponse:
        pass

    @abstractmethod
    def stream_generate(
        self, prompt: str, model: str = None, **kwargs
    ) -> Generator[str, None, None]:
        pass

    def close(self):
        self.client.close()


class OpenRouterClient(BaseAPIClient):
    def __init__(self, api_key: str):
        super().__init__(api_key, "https://openrouter.ai/api/v1")

    def generate(
        self,
        prompt: str,
        model: str = "meta-llama/llama-3.2-3b-instruct:free",
        **kwargs,
    ) -> APIResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/promptconsole/promptconsole",
            "X-Title": "PromptConsole",
        }

        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            **kwargs,
        }

        response = self.client.post(
            f"{self.base_url}/chat/completions", headers=headers, json=data
        )
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]
        usage = result.get("usage")

        return APIResponse(
            content=content,
            model=model,
            usage=usage,
            provider="openrouter",
            raw_response=result,
        )

    def stream_generate(
        self,
        prompt: str,
        model: str = "meta-llama/llama-3.2-3b-instruct:free",
        **kwargs,
    ) -> Generator[str, None, None]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/promptconsole/promptconsole",
            "X-Title": "PromptConsole",
        }

        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            **kwargs,
        }

        with self.client.stream(
            "POST", f"{self.base_url}/chat/completions", headers=headers, json=data
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        if "choices" in chunk and chunk["choices"]:
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue


class OpenAIClient(BaseAPIClient):
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        super().__init__(api_key, base_url)
        self.is_openrouter = "openrouter.ai" in base_url

    def generate(
        self, prompt: str, model: str = "gpt-3.5-turbo", **kwargs
    ) -> APIResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if self.is_openrouter:
            headers.update(
                {
                    "HTTP-Referer": "https://github.com/promptconsole/promptconsole",
                    "X-Title": "PromptConsole",
                }
            )

        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            **kwargs,
        }

        response = self.client.post(
            f"{self.base_url}/chat/completions", headers=headers, json=data
        )
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]
        usage = result.get("usage")

        provider_name = "openrouter" if self.is_openrouter else "openai"
        return APIResponse(
            content=content,
            model=model,
            usage=usage,
            provider=provider_name,
            raw_response=result,
        )

    def stream_generate(
        self, prompt: str, model: str = "gpt-3.5-turbo", **kwargs
    ) -> Generator[str, None, None]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if self.is_openrouter:
            headers.update(
                {
                    "HTTP-Referer": "https://github.com/promptconsole/promptconsole",
                    "X-Title": "PromptConsole",
                }
            )

        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            **kwargs,
        }

        with self.client.stream(
            "POST", f"{self.base_url}/chat/completions", headers=headers, json=data
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        if "choices" in chunk and chunk["choices"]:
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue


class CustomAPIClient(BaseAPIClient):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        headers: Dict[str, str] = None,
        provider_name: str = "custom",
        auth_type: str = "bearer",
    ):
        super().__init__(api_key, base_url)
        self.custom_headers = headers or {}
        self.provider_name = provider_name
        self.auth_type = auth_type

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers based on auth_type."""
        if self.auth_type == "bearer":
            return {"Authorization": f"Bearer {self.api_key}"}
        elif self.auth_type == "api-key":
            return {"Authorization": f"Api-Key {self.api_key}"}
        elif self.auth_type == "x-api-key":
            return {"X-API-Key": self.api_key}
        else:
            # Default to bearer if unknown auth_type
            return {"Authorization": f"Bearer {self.api_key}"}

    def generate(self, prompt: str, model: str = None, **kwargs) -> APIResponse:
        # Build authentication header based on auth_type
        auth_headers = self._get_auth_headers()

        headers = {
            "Content-Type": "application/json",
            **auth_headers,
            **self.custom_headers,
        }

        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            **kwargs,
        }

        try:
            response = self.client.post(
                f"{self.base_url}/chat/completions", headers=headers, json=data
            )
            response.raise_for_status()

            result = response.json()

            # Handle different response formats more robustly
            if "choices" not in result or not result["choices"]:
                raise ValueError(
                    f"Invalid response format from {self.provider_name}: missing 'choices'"
                )

            choice = result["choices"][0]
            if "message" not in choice:
                raise ValueError(
                    f"Invalid response format from {self.provider_name}: missing 'message' in choice"
                )

            content = choice["message"].get("content", "")
            usage = result.get("usage")

            return APIResponse(
                content=content,
                model=model,
                usage=usage,
                provider=self.provider_name,
                raw_response=result,
            )
        except httpx.TimeoutException as e:
            raise ValueError(f"Request to {self.provider_name} timed out: {e}")
        except httpx.HTTPStatusError as e:
            raise ValueError(
                f"HTTP error from {self.provider_name}: {e.response.status_code} - {e.response.text}"
            )
        except httpx.RequestError as e:
            raise ValueError(f"Request error to {self.provider_name}: {e}")
        except Exception as e:
            raise ValueError(f"Unexpected error with {self.provider_name}: {e}")

    def stream_generate(
        self, prompt: str, model: str = None, **kwargs
    ) -> Generator[str, None, None]:
        # Build authentication header based on auth_type
        auth_headers = self._get_auth_headers()

        headers = {
            "Content-Type": "application/json",
            **auth_headers,
            **self.custom_headers,
        }

        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            **kwargs,
        }

        try:
            with self.client.stream(
                "POST", f"{self.base_url}/chat/completions", headers=headers, json=data
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            if "choices" in chunk and chunk["choices"]:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
        except httpx.TimeoutException as e:
            raise ValueError(
                f"Streaming request to {self.provider_name} timed out: {e}"
            )
        except httpx.HTTPStatusError as e:
            raise ValueError(
                f"HTTP error during streaming from {self.provider_name}: {e.response.status_code}"
            )
        except httpx.RequestError as e:
            raise ValueError(
                f"Request error during streaming to {self.provider_name}: {e}"
            )
        except Exception as e:
            raise ValueError(
                f"Unexpected error during streaming with {self.provider_name}: {e}"
            )


class AnthropicClient(BaseAPIClient):
    def __init__(self, api_key: str):
        super().__init__(api_key, "https://api.anthropic.com/v1")

    def generate(
        self, prompt: str, model: str = "claude-3-haiku-20240307", **kwargs
    ) -> APIResponse:
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        data = {
            "model": model,
            "max_tokens": kwargs.get("max_tokens", 1024),
            "messages": [{"role": "user", "content": prompt}],
            **{k: v for k, v in kwargs.items() if k != "max_tokens"},
        }

        response = self.client.post(
            f"{self.base_url}/messages", headers=headers, json=data
        )
        response.raise_for_status()

        result = response.json()
        content = result["content"][0]["text"]
        usage = result.get("usage")

        return APIResponse(
            content=content,
            model=model,
            usage=usage,
            provider="anthropic",
            raw_response=result,
        )

    def stream_generate(
        self, prompt: str, model: str = "claude-3-haiku-20240307", **kwargs
    ) -> Generator[str, None, None]:
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        data = {
            "model": model,
            "max_tokens": kwargs.get("max_tokens", 1024),
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            **{k: v for k, v in kwargs.items() if k not in ["max_tokens"]},
        }

        with self.client.stream(
            "POST", f"{self.base_url}/messages", headers=headers, json=data
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        chunk = json.loads(data_str)
                        if chunk.get("type") == "content_block_delta":
                            text = chunk.get("delta", {}).get("text", "")
                            if text:
                                yield text
                    except json.JSONDecodeError:
                        continue


def get_client(
    provider: str, api_key: str, custom_config: Dict[str, Any] = None
) -> BaseAPIClient:
    """Factory function to get the appropriate API client."""
    if provider == "openrouter":
        # Use OpenAI client with OpenRouter endpoint
        return OpenAIClient(api_key, "https://openrouter.ai/api/v1")
    elif provider == "openai":
        return OpenAIClient(api_key)
    elif provider == "anthropic":
        return AnthropicClient(api_key)
    elif provider == "custom":
        if not custom_config:
            raise ValueError("Custom provider requires configuration")
        return CustomAPIClient(
            api_key=api_key,
            base_url=custom_config["base_url"],
            headers=custom_config.get("headers", {}),
            provider_name=custom_config.get("name", "custom"),
            auth_type=custom_config.get("auth_type", "bearer"),
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")
