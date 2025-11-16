"""Simplified LLM adapter wrapper for easy integration."""

from typing import Optional
from app.services.llm import LLMFactory, LLMMessage, LLMConfig, BaseLLMAdapter
from app.core.config import settings


class LLMAdapter:
    """
    Simplified wrapper around LLM factory for easy text generation.

    Provides a simple interface for generating text without needing to manage
    factory patterns, message objects, or provider-specific configurations.
    """

    def __init__(self):
        """Initialize the LLM adapter."""
        self._adapters = {}  # Cache adapters by provider

    def _get_api_key(self, provider: str) -> str:
        """
        Get API key for the specified provider.

        Args:
            provider: LLM provider name

        Returns:
            API key for the provider

        Raises:
            ValueError: If API key is not configured
        """
        provider_lower = provider.lower()

        if provider_lower == "openai":
            api_key = settings.OPENAI_API_KEY
        elif provider_lower == "anthropic":
            api_key = settings.ANTHROPIC_API_KEY
        elif provider_lower == "huggingface":
            api_key = settings.HUGGINGFACE_API_KEY
        else:
            raise ValueError(f"Unknown provider: {provider}")

        if not api_key:
            raise ValueError(
                f"API key not configured for {provider}. "
                f"Please set {provider.upper()}_API_KEY in your environment."
            )

        return api_key

    def _get_adapter(self, provider: str) -> BaseLLMAdapter:
        """
        Get or create an adapter for the specified provider.

        Args:
            provider: LLM provider name

        Returns:
            LLM adapter instance
        """
        # Cache adapters to avoid recreating them
        if provider not in self._adapters:
            api_key = self._get_api_key(provider)
            self._adapters[provider] = LLMFactory.create(
                provider=provider,
                api_key=api_key
            )

        return self._adapters[provider]

    async def generate(
        self,
        prompt: str,
        provider: str = "openai",
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        model: Optional[str] = None
    ) -> str:
        """
        Generate text from a prompt using the specified LLM provider.

        Args:
            prompt: User prompt to generate from
            provider: LLM provider to use (openai, anthropic, huggingface)
            system_prompt: Optional system instructions
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 2.0)
            model: Optional specific model to use (uses provider default if not specified)

        Returns:
            Generated text content

        Raises:
            ValueError: If provider is invalid or API key not configured
            LLMException: If generation fails
        """
        # Get the appropriate adapter
        adapter = self._get_adapter(provider)

        # Create configuration
        if model is None:
            # Use default model for the provider
            models = adapter.get_models()
            model = models[0] if models else "default"

        config = LLMConfig(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature
        )

        # Generate text using the adapter
        response = await adapter.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            config=config
        )

        return response

    async def generate_with_messages(
        self,
        messages: list[dict],
        provider: str = "openai",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        model: Optional[str] = None
    ) -> str:
        """
        Generate text from a conversation history.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            provider: LLM provider to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            model: Optional specific model to use

        Returns:
            Generated text content

        Raises:
            ValueError: If provider is invalid or API key not configured
            LLMException: If generation fails
        """
        # Get the appropriate adapter
        adapter = self._get_adapter(provider)

        # Convert dict messages to LLMMessage objects
        llm_messages = [
            LLMMessage(role=msg["role"], content=msg["content"])
            for msg in messages
        ]

        # Create configuration
        if model is None:
            models = adapter.get_models()
            model = models[0] if models else "default"

        config = LLMConfig(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature
        )

        # Generate using the adapter
        response = await adapter.generate(
            messages=llm_messages,
            config=config
        )

        return response.content

    def get_available_providers(self) -> list[str]:
        """
        Get list of available LLM providers.

        Returns:
            List of provider names
        """
        return LLMFactory.get_available_providers()

    def get_provider_models(self, provider: str) -> list[str]:
        """
        Get available models for a provider.

        Args:
            provider: Provider name

        Returns:
            List of model names
        """
        return LLMFactory.get_provider_models(provider)

    async def generate_text(
        self,
        prompt: str,
        provider: str = "openai",
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        model: Optional[str] = None
    ) -> str:
        """
        Alias for generate() method for clarity.

        Args:
            prompt: User prompt to generate from
            provider: LLM provider to use
            system_prompt: Optional system instructions
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            model: Optional specific model to use

        Returns:
            Generated text content
        """
        return await self.generate(
            prompt=prompt,
            provider=provider,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            model=model
        )

    async def generate_embedding(
        self,
        text: str,
        provider: str = "openai",
        model: Optional[str] = None
    ) -> list[float]:
        """
        Generate text embedding vector.

        Args:
            text: Text to embed
            provider: LLM provider (currently only OpenAI supported)
            model: Optional embedding model (default: text-embedding-3-small)

        Returns:
            Embedding vector as list of floats

        Raises:
            ValueError: If provider doesn't support embeddings
        """
        if provider.lower() != "openai":
            raise ValueError(
                f"Embeddings currently only supported for OpenAI. "
                f"Provider '{provider}' not supported."
            )

        # Use OpenAI embeddings API
        import openai

        api_key = self._get_api_key(provider)
        client = openai.AsyncOpenAI(api_key=api_key)

        # Use efficient small model by default
        embedding_model = model or "text-embedding-3-small"

        response = await client.embeddings.create(
            input=text,
            model=embedding_model
        )

        # Extract embedding vector
        embedding = response.data[0].embedding

        return embedding


# Singleton instance
llm_adapter = LLMAdapter()
