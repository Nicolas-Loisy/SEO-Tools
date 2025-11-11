"""OpenAI LLM adapter."""

from typing import List, Optional, Dict, Any
from openai import AsyncOpenAI
from openai import RateLimitError, AuthenticationError, APIError

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


class OpenAIAdapter(BaseLLMAdapter):
    """
    Adapter for OpenAI API (GPT-4, GPT-3.5).

    Supports:
    - GPT-4 Turbo
    - GPT-4
    - GPT-3.5 Turbo
    """

    MODELS = [
        "gpt-4-turbo-preview",
        "gpt-4-1106-preview",
        "gpt-4",
        "gpt-3.5-turbo-1106",
        "gpt-3.5-turbo",
    ]

    DEFAULT_MODEL = "gpt-3.5-turbo-1106"

    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        """Initialize OpenAI adapter."""
        super().__init__(api_key, config)
        self.client = AsyncOpenAI(api_key=api_key)

    def _get_provider(self) -> LLMProvider:
        """Get provider type."""
        return LLMProvider.OPENAI

    async def generate(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig] = None,
    ) -> LLMResponse:
        """
        Generate completion using OpenAI Chat API.

        Args:
            messages: Conversation messages
            config: Generation configuration

        Returns:
            LLMResponse with generated content
        """
        config = config or LLMConfig(model=self.DEFAULT_MODEL)
        self.validate_config(config)

        # Convert messages to OpenAI format
        openai_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        try:
            response = await self.client.chat.completions.create(
                model=config.model,
                messages=openai_messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
                frequency_penalty=config.frequency_penalty,
                presence_penalty=config.presence_penalty,
                stop=config.stop,
            )

            choice = response.choices[0]

            return LLMResponse(
                content=choice.message.content,
                model=response.model,
                provider=self.provider.value,
                tokens_used=response.usage.total_tokens,
                finish_reason=choice.finish_reason,
                metadata={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                },
            )

        except RateLimitError as e:
            raise LLMRateLimitException(
                message="OpenAI rate limit exceeded",
                provider=self.provider.value,
                original_error=e,
            )
        except AuthenticationError as e:
            raise LLMAuthenticationException(
                message="OpenAI authentication failed",
                provider=self.provider.value,
                original_error=e,
            )
        except APIError as e:
            raise LLMException(
                message=f"OpenAI API error: {str(e)}",
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

        Uses rough estimation: ~4 characters per token for English.

        Args:
            text: Text to count

        Returns:
            Estimated token count
        """
        # Rough estimation for English text
        # For accurate counting, use tiktoken library
        return len(text) // 4

    def get_models(self) -> List[str]:
        """Get available OpenAI models."""
        return self.MODELS
