"""Tests for LLM factory."""

import pytest
from app.services.llm import LLMFactory, LLMProvider
from app.services.llm.openai_adapter import OpenAIAdapter
from app.services.llm.anthropic_adapter import AnthropicAdapter
from app.services.llm.huggingface_adapter import HuggingFaceAdapter


def test_create_openai_adapter():
    """Test creating OpenAI adapter."""
    adapter = LLMFactory.create(provider="openai", api_key="test_key")
    assert isinstance(adapter, OpenAIAdapter)
    assert adapter.provider == LLMProvider.OPENAI


def test_create_anthropic_adapter():
    """Test creating Anthropic adapter."""
    adapter = LLMFactory.create(provider="anthropic", api_key="test_key")
    assert isinstance(adapter, AnthropicAdapter)
    assert adapter.provider == LLMProvider.ANTHROPIC


def test_create_huggingface_adapter():
    """Test creating HuggingFace adapter."""
    adapter = LLMFactory.create(provider="huggingface", api_key="test_key")
    assert isinstance(adapter, HuggingFaceAdapter)
    assert adapter.provider == LLMProvider.HUGGINGFACE


def test_create_invalid_provider():
    """Test creating adapter with invalid provider."""
    with pytest.raises(ValueError) as exc_info:
        LLMFactory.create(provider="invalid", api_key="test_key")
    assert "Unknown LLM provider" in str(exc_info.value)


def test_get_available_providers():
    """Test getting list of available providers."""
    providers = LLMFactory.get_available_providers()
    assert "openai" in providers
    assert "anthropic" in providers
    assert "huggingface" in providers


def test_get_provider_models():
    """Test getting models for each provider."""
    # OpenAI
    models = LLMFactory.get_provider_models("openai")
    assert "gpt-3.5-turbo" in models
    assert "gpt-4" in models

    # Anthropic
    models = LLMFactory.get_provider_models("anthropic")
    assert any("claude" in m for m in models)

    # HuggingFace
    models = LLMFactory.get_provider_models("huggingface")
    assert any("mistral" in m.lower() for m in models)
