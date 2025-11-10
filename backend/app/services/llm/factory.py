"""LLM factory implementing Strategy pattern."""

from typing import Dict, Any, Optional
from app.services.llm.base import BaseLLMAdapter, LLMProvider
from app.services.llm.openai_adapter import OpenAIAdapter
from app.services.llm.anthropic_adapter import AnthropicAdapter
from app.services.llm.huggingface_adapter import HuggingFaceAdapter


class LLMFactory:
    """
    Factory for creating LLM adapters based on provider.

    Implements Strategy Pattern for interchangeable LLM backends.
    """

    @staticmethod
    def create(
        provider: str,
        api_key: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> BaseLLMAdapter:
        """
        Create an LLM adapter instance based on provider.

        Args:
            provider: Provider name ("openai", "anthropic", "huggingface")
            api_key: API key for the provider
            config: Additional configuration options

        Returns:
            LLM adapter instance

        Raises:
            ValueError: If provider is unknown
        """
        provider_lower = provider.lower()

        if provider_lower == LLMProvider.OPENAI.value:
            return OpenAIAdapter(api_key=api_key, config=config)

        elif provider_lower == LLMProvider.ANTHROPIC.value:
            return AnthropicAdapter(api_key=api_key, config=config)

        elif provider_lower == LLMProvider.HUGGINGFACE.value:
            return HuggingFaceAdapter(api_key=api_key, config=config)

        else:
            raise ValueError(
                f"Unknown LLM provider: {provider}. "
                f"Use one of: {', '.join([p.value for p in LLMProvider])}"
            )

    @staticmethod
    def get_available_providers() -> list[str]:
        """
        Get list of available LLM providers.

        Returns:
            List of provider names
        """
        return [provider.value for provider in LLMProvider]

    @staticmethod
    def get_provider_models(provider: str) -> list[str]:
        """
        Get available models for a provider.

        Args:
            provider: Provider name

        Returns:
            List of model names

        Raises:
            ValueError: If provider is unknown
        """
        provider_lower = provider.lower()

        if provider_lower == LLMProvider.OPENAI.value:
            return OpenAIAdapter.MODELS

        elif provider_lower == LLMProvider.ANTHROPIC.value:
            return AnthropicAdapter.MODELS

        elif provider_lower == LLMProvider.HUGGINGFACE.value:
            return HuggingFaceAdapter.MODELS

        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
