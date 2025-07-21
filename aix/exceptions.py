"""Custom exceptions for aix API clients."""


class AIXError(Exception):
    """Base exception for all aix errors."""
    
    def __init__(self, message: str, provider: str = None, status_code: int = None):
        self.message = message
        self.provider = provider
        self.status_code = status_code
        super().__init__(message)


class APIError(AIXError):
    """Base API error."""
    pass


class AuthenticationError(APIError):
    """API key authentication failed."""
    pass


class InsufficientCreditsError(APIError):
    """Not enough credits/balance to complete request."""
    pass


class ModelNotFoundError(APIError):
    """Requested model not found or unavailable."""
    pass


class RateLimitError(APIError):
    """API rate limit exceeded."""
    pass


class InvalidRequestError(APIError):
    """Invalid request parameters."""
    pass


class ProviderError(APIError):
    """Provider-specific error."""
    pass


def parse_api_error(response, provider: str) -> AIXError:
    """Parse HTTP response and return appropriate exception."""
    status_code = response.status_code
    
    try:
        error_data = response.json()
        error_message = error_data.get("error", {})
        
        # Handle different error response formats
        if isinstance(error_message, dict):
            message = error_message.get("message", "Unknown error")
            error_type = error_message.get("type", "")
            error_code = error_message.get("code", status_code)
            
            # Check for nested error metadata (OpenRouter format)
            metadata = error_message.get("metadata", {})
            if metadata and "raw" in metadata:
                try:
                    import json
                    raw_error = json.loads(metadata["raw"])
                    if isinstance(raw_error, dict) and "error" in raw_error:
                        # Use the nested error message for better context
                        nested_message = raw_error["error"]
                        if nested_message:
                            message = f"{message}: {nested_message}"
                except (json.JSONDecodeError, KeyError):
                    pass
        else:
            message = str(error_message) if error_message else f"HTTP {status_code}"
            error_type = ""
            error_code = status_code
            
    except (ValueError, KeyError):
        message = f"HTTP {status_code}: {response.text[:200]}"
        error_type = ""
        error_code = status_code
    
    # Map status codes and error types to specific exceptions
    if status_code == 401:
        return AuthenticationError(
            f"Invalid API key for {provider}. Please check your API key configuration.",
            provider=provider,
            status_code=status_code
        )
    
    elif status_code == 402 or "insufficient" in message.lower() or "balance" in message.lower() or "usd" in message.lower() or "diem" in message.lower():
        return InsufficientCreditsError(
            f"Insufficient credits for {provider}. Please add credits to your account.",
            provider=provider,
            status_code=status_code
        )
    
    elif status_code == 429 or "rate limit" in message.lower():
        return RateLimitError(
            f"Rate limit exceeded for {provider}. Please wait and try again.",
            provider=provider,
            status_code=status_code
        )
    
    elif status_code == 404 or "not found" in message.lower() or "no endpoints" in message.lower():
        return ModelNotFoundError(
            f"Model not available on {provider}. Try a different model or check the provider's available models.",
            provider=provider,
            status_code=status_code
        )
    
    elif status_code >= 400 and status_code < 500:
        return InvalidRequestError(
            f"Invalid request to {provider}: {message}",
            provider=provider,
            status_code=status_code
        )
    
    elif status_code >= 500:
        return ProviderError(
            f"{provider} server error: {message}. Please try again later.",
            provider=provider,
            status_code=status_code
        )
    
    else:
        return APIError(
            f"{provider} error: {message}",
            provider=provider,
            status_code=status_code
        )