"""HuggingFace LLM adapter."""

from typing import List, Optional, Dict, Any
import httpx

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


class HuggingFaceAdapter(BaseLLMAdapter):
    """
    Adapter for HuggingFace Inference API.

    Supports:
    - Mistral 7B
    - Llama 2
    - Falcon
    - And many other open-source models
    """

    MODELS = [
        "mistralai/Mistral-7B-Instruct-v0.2",
        "meta-llama/Llama-2-70b-chat-hf",
        "meta-llama/Llama-2-13b-chat-hf",
        "tiiuae/falcon-40b-instruct",
        "HuggingFaceH4/zephyr-7b-beta",
    ]

    DEFAULT_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
    API_URL = "https://api-inference.huggingface.co/models"

    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        """Initialize HuggingFace adapter."""
        super().__init__(api_key, config)
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def _get_provider(self) -> LLMProvider:
        """Get provider type."""
        return LLMProvider.HUGGINGFACE

    async def generate(
        self,
        messages: List[LLMMessage],
        config: Optional[LLMConfig] = None,
    ) -> LLMResponse:
        """
        Generate completion using HuggingFace Inference API.

        Args:
            messages: Conversation messages
            config: Generation configuration

        Returns:
            LLMResponse with generated content
        """
        config = config or LLMConfig(model=self.DEFAULT_MODEL)
        self.validate_config(config)

        # Convert messages to prompt format
        prompt = self._messages_to_prompt(messages, config.model)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.API_URL}/{config.model}",
                    headers=self.headers,
                    json={
                        "inputs": prompt,
                        "parameters": {
                            "max_new_tokens": config.max_tokens,
                            "temperature": config.temperature,
                            "top_p": config.top_p,
                            "do_sample": True,
                            "return_full_text": False,
                        },
                    },
                    timeout=60.0,
                )

                if response.status_code == 401:
                    raise LLMAuthenticationException(
                        message="HuggingFace authentication failed",
                        provider=self.provider.value,
                    )
                elif response.status_code == 429:
                    raise LLMRateLimitException(
                        message="HuggingFace rate limit exceeded",
                        provider=self.provider.value,
                    )
                elif response.status_code != 200:
                    raise LLMException(
                        message=f"HuggingFace API error: {response.status_code} - {response.text}",
                        provider=self.provider.value,
                    )

                result = response.json()

                # Handle different response formats
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get("generated_text", "")
                elif isinstance(result, dict):
                    generated_text = result.get("generated_text", "")
                else:
                    generated_text = str(result)

                # Estimate tokens (rough)
                tokens_used = await self.count_tokens(prompt + generated_text)

                return LLMResponse(
                    content=generated_text.strip(),
                    model=config.model,
                    provider=self.provider.value,
                    tokens_used=tokens_used,
                    finish_reason="stop",  # HF doesn't always provide this
                    metadata={
                        "prompt": prompt,
                    },
                )

        except httpx.HTTPError as e:
            raise LLMException(
                message=f"HuggingFace HTTP error: {str(e)}",
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

    def _messages_to_prompt(self, messages: List[LLMMessage], model: str) -> str:
        """
        Convert messages to prompt format for the model.

        Different models use different chat templates.

        Args:
            messages: Conversation messages
            model: Model name

        Returns:
            Formatted prompt string
        """
        # Mistral/Llama 2 format
        if "mistral" in model.lower() or "llama" in model.lower():
            prompt_parts = []
            for msg in messages:
                if msg.role == "system":
                    prompt_parts.append(f"<s>[INST] {msg.content} [/INST]")
                elif msg.role == "user":
                    if not prompt_parts:
                        prompt_parts.append(f"<s>[INST] {msg.content} [/INST]")
                    else:
                        prompt_parts.append(f"[INST] {msg.content} [/INST]")
                elif msg.role == "assistant":
                    prompt_parts.append(f" {msg.content}</s>")
            return "".join(prompt_parts)

        # Falcon format
        elif "falcon" in model.lower():
            prompt_parts = []
            for msg in messages:
                if msg.role == "system":
                    prompt_parts.append(f"System: {msg.content}\n")
                elif msg.role == "user":
                    prompt_parts.append(f"User: {msg.content}\n")
                elif msg.role == "assistant":
                    prompt_parts.append(f"Assistant: {msg.content}\n")
            prompt_parts.append("Assistant:")
            return "".join(prompt_parts)

        # Default format
        else:
            prompt_parts = []
            for msg in messages:
                prompt_parts.append(f"{msg.role.capitalize()}: {msg.content}\n")
            return "\n".join(prompt_parts)

    async def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Args:
            text: Text to count

        Returns:
            Estimated token count
        """
        # Rough estimation for most models
        return len(text) // 4

    def get_models(self) -> List[str]:
        """Get available HuggingFace models."""
        return self.MODELS
