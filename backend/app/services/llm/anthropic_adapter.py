"""Anthropic Claude LLM adapter."""

from typing import List, Optional, Dict, Any
from anthropic import AsyncAnthropic, RateLimitError, AuthenticationError, APIError

from app.services.llm.base import (
    BaseLLMAdapter,
    LLMMessage,
    LLMResponse,
    LLMConfig,
    LLMProvider,
    LLMException,
    LLMRateLimitException,
    LLMAuthenticationException,
)


class AnthropicAdapter(BaseLLMAdapter):
    """
    Adapter for Anthropic Claude API.

    Supports:
    - Claude 3 Opus
    - Claude 3 Sonnet
    - Claude 3 Haiku
    - Claude 2.1
    """

    MODELS = [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-2.1",
        "claude-2.0",
    ]

    DEFAULT_MODEL = "claude-3-sonnet-20240229"

    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        """Initialize Anthropic adapter."""
        super().__init__(api_key, config)
        self.client = AsyncAnthropic(api_key=api_key)

    def _get_provider(self) -> LLMProvider:
        """Get provider type."""
        return LLMProvider.ANTHROPIC

    async def generate(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig] = None,
    ) -> LLMResponse:
        """
        Generate completion using Anthropic Messages API.

        Args:
            messages: Conversation messages
            config: Generation configuration

        Returns:
            LLMResponse with generated content
        """
        config = config or LLMConfig(model=self.DEFAULT_MODEL)
        self.validate_config(config)

        # Separate system message from conversation
        system_message = None
        conversation_messages = []

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                conversation_messages.append({"role": msg.role, "content": msg.content})

        try:
            # Build request parameters
            request_params = {
                "model": config.model,
                "messages": conversation_messages,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "top_p": config.top_p,
            }

            if system_message:
                request_params["system"] = system_message

            if config.stop:
                request_params["stop_sequences"] = config.stop

            response = await self.client.messages.create(**request_params)

            # Extract content from response
            content = response.content[0].text if response.content else ""

            return LLMResponse(
                content=content,
                model=response.model,
                provider=self.provider.value,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                finish_reason=response.stop_reason,
                metadata={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
            )

        except RateLimitError as e:
            raise LLMRateLimitException(
                message="Anthropic rate limit exceeded",
                provider=self.provider.value,
                original_error=e,
            )
        except AuthenticationError as e:
            raise LLMAuthenticationException(
                message="Anthropic authentication failed",
                provider=self.provider.value,
                original_error=e,
            )
        except APIError as e:
            raise LLMException(
                message=f"Anthropic API error: {str(e)}",
                provider=self.provider.value,
                original_error=e,
            )

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        config: Optional[LLMConfig] = None,
    ) -> str:
        """
        Generate text from simple prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system instructions
            config: Generation configuration

        Returns:
            Generated text
        """
        messages = []

        if system_prompt:
            messages.append(LLMMessage(role="system", content=system_prompt))

        messages.append(LLMMessage(role="user", content=prompt))

        response = await self.generate(messages, config)
        return response.content

    async def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Uses rough estimation: ~4 characters per token.

        Args:
            text: Text to count

        Returns:
            Estimated token count
        """
        # Anthropic doesn't provide a token counter API
        # Use rough estimation similar to OpenAI
        return len(text) // 4

    def get_models(self) -> List[str]:
        """Get available Anthropic models."""
        return self.MODELS
