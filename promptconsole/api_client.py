import httpx
import json
from typing import Dict, Any, Optional, AsyncGenerator, Generator
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class Provider(Enum):
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    TOGETHER = "together"

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
    def stream_generate(self, prompt: str, model: str = None, **kwargs) -> Generator[str, None, None]:
        pass
    
    def close(self):
        self.client.close()

class OpenRouterClient(BaseAPIClient):
    def __init__(self, api_key: str):
        super().__init__(api_key, "https://openrouter.ai/api/v1")
    
    def generate(self, prompt: str, model: str = "meta-llama/llama-3.2-3b-instruct:free", **kwargs) -> APIResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/promptconsole/promptconsole",
            "X-Title": "PromptConsole"
        }
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            **kwargs
        }
        
        response = self.client.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data
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
            raw_response=result
        )
    
    def stream_generate(self, prompt: str, model: str = "meta-llama/llama-3.2-3b-instruct:free", **kwargs) -> Generator[str, None, None]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/promptconsole/promptconsole",
            "X-Title": "PromptConsole"
        }
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            **kwargs
        }
        
        with self.client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data
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
    
    def generate(self, prompt: str, model: str = "gpt-3.5-turbo", **kwargs) -> APIResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if self.is_openrouter:
            headers.update({
                "HTTP-Referer": "https://github.com/promptconsole/promptconsole",
                "X-Title": "PromptConsole"
            })
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            **kwargs
        }
        
        response = self.client.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data
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
            raw_response=result
        )
    
    def stream_generate(self, prompt: str, model: str = "gpt-3.5-turbo", **kwargs) -> Generator[str, None, None]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if self.is_openrouter:
            headers.update({
                "HTTP-Referer": "https://github.com/promptconsole/promptconsole",
                "X-Title": "PromptConsole"
            })
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            **kwargs
        }
        
        with self.client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data
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

class AnthropicClient(BaseAPIClient):
    def __init__(self, api_key: str):
        super().__init__(api_key, "https://api.anthropic.com/v1")
    
    def generate(self, prompt: str, model: str = "claude-3-haiku-20240307", **kwargs) -> APIResponse:
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": model,
            "max_tokens": kwargs.get("max_tokens", 1024),
            "messages": [{"role": "user", "content": prompt}],
            **{k: v for k, v in kwargs.items() if k != "max_tokens"}
        }
        
        response = self.client.post(
            f"{self.base_url}/messages",
            headers=headers,
            json=data
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
            raw_response=result
        )
    
    def stream_generate(self, prompt: str, model: str = "claude-3-haiku-20240307", **kwargs) -> Generator[str, None, None]:
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": model,
            "max_tokens": kwargs.get("max_tokens", 1024),
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
            **{k: v for k, v in kwargs.items() if k not in ["max_tokens"]}
        }
        
        with self.client.stream(
            "POST",
            f"{self.base_url}/messages",
            headers=headers,
            json=data
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

def get_client(provider: str, api_key: str) -> BaseAPIClient:
    """Factory function to get the appropriate API client."""
    if provider == "openrouter":
        # Use OpenAI client with OpenRouter endpoint
        return OpenAIClient(api_key, "https://openrouter.ai/api/v1")
    elif provider == "openai":
        return OpenAIClient(api_key)
    elif provider == "anthropic":
        return AnthropicClient(api_key)
    else:
        raise ValueError(f"Unsupported provider: {provider}")