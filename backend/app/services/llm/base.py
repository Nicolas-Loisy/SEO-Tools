"""Base LLM adapter interface implementing Strategy pattern."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"


@dataclass
class LLMMessage:
    """Message in LLM conversation."""

    role: str  # system, user, assistant
    content: str


@dataclass
class LLMResponse:
    """Response from LLM."""

    content: str
    model: str
    provider: str
    tokens_used: int
    finish_reason: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMConfig:
    """Configuration for LLM requests."""

    model: str
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[List[str]] = None


class BaseLLMAdapter(ABC):
    """
    Base adapter for LLM providers.

    Implements Strategy pattern for interchangeable LLM backends.
    """

    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LLM adapter.

        Args:
            api_key: API key for the provider
            config: Additional configuration options
        """
        self.api_key = api_key
        self.config = config or {}
        self.provider = self._get_provider()

    @abstractmethod
    def _get_provider(self) -> LLMProvider:
        """Get the provider type."""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig] = None,
    ) -> LLMResponse:
        """
        Generate completion from messages.

        Args:
            messages: List of conversation messages
            config: Generation configuration

        Returns:
            LLMResponse with generated content

        Raises:
            LLMException: If generation fails
        """
        pass

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[LLMConfig] = None,
    ) -> str:
        """
        Generate text from a simple prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system instructions
            config: Generation configuration

        Returns:
            Generated text content

        Raises:
            LLMException: If generation fails
        """
        pass

    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count

        Returns:
            Number of tokens
        """
        pass

    @abstractmethod
    def get_models(self) -> List[str]:
        """
        Get list of available models for this provider.

        Returns:
            List of model names
        """
        pass

    def validate_config(self, config: LLMConfig) -> bool:
        """
        Validate configuration parameters.

        Args:
            config: Configuration to validate

        Returns:
            True if valid

        Raises:
            ValueError: If configuration is invalid
        """
        if config.temperature < 0 or config.temperature > 2:
            raise ValueError("Temperature must be between 0 and 2")

        if config.max_tokens < 1:
            raise ValueError("max_tokens must be positive")

        if config.top_p < 0 or config.top_p > 1:
            raise ValueError("top_p must be between 0 and 1")

        return True


class LLMException(Exception):
    """Base exception for LLM errors."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        self.message = message
        self.provider = provider
        self.original_error = original_error
        super().__init__(self.message)


class LLMRateLimitException(LLMException):
    """Raised when LLM rate limit is exceeded."""

    pass


class LLMAuthenticationException(LLMException):
    """Raised when LLM authentication fails."""

    pass


class LLMContentFilterException(LLMException):
    """Raised when content is filtered by safety systems."""

    pass
