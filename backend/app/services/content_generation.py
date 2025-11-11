"""Content generation service using LLM adapters."""

from typing import Optional, Dict, Any
from app.services.llm import LLMFactory, LLMConfig, LLMMessage
from app.models.page import Page


class ContentGenerationService:
    """
    Service for generating SEO-optimized content using LLMs.

    Supports:
    - Meta description generation
    - Title tag optimization
    - H1 suggestions
    - Content recommendations
    """

    def __init__(
        self,
        provider: str = "openai",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize content generation service.

        Args:
            provider: LLM provider ("openai", "anthropic", "huggingface")
            api_key: API key for the provider
            model: Optional specific model to use
        """
        if not api_key:
            raise ValueError("API key is required for content generation")

        self.llm = LLMFactory.create(provider=provider, api_key=api_key)
        self.provider = provider
        self.model = model

    async def generate_meta_description(
        self,
        page: Page,
        max_length: int = 160,
        language: str = "en",
    ) -> str:
        """
        Generate SEO-optimized meta description for a page.

        Args:
            page: Page object with content
            max_length: Maximum description length (default: 160 chars)
            language: Content language

        Returns:
            Generated meta description
        """
        # Build prompt
        system_prompt = self._get_system_prompt(language)

        user_prompt = f"""Generate a compelling meta description for this webpage.

URL: {page.url}
Title: {page.title or 'N/A'}
H1: {page.h1 or 'N/A'}

Content excerpt:
{page.text_content[:500] if page.text_content else 'No content'}

Requirements:
- Maximum {max_length} characters
- Include primary keywords naturally
- Compelling call-to-action
- No clickbait
- Language: {language}

Meta description:"""

        config = LLMConfig(
            model=self.model or self._get_default_model(),
            temperature=0.7,
            max_tokens=100,
        )

        description = await self.llm.generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt,
            config=config,
        )

        # Clean and truncate
        description = description.strip().strip('"\'')
        if len(description) > max_length:
            description = description[:max_length - 3] + "..."

        return description

    async def generate_title_suggestions(
        self,
        page: Page,
        count: int = 3,
        max_length: int = 60,
        language: str = "en",
    ) -> list[str]:
        """
        Generate SEO-optimized title tag suggestions.

        Args:
            page: Page object
            count: Number of suggestions to generate
            max_length: Maximum title length (default: 60 chars)
            language: Content language

        Returns:
            List of title suggestions
        """
        system_prompt = self._get_system_prompt(language)

        user_prompt = f"""Generate {count} SEO-optimized title tags for this webpage.

URL: {page.url}
Current Title: {page.title or 'N/A'}
H1: {page.h1 or 'N/A'}

Content excerpt:
{page.text_content[:500] if page.text_content else 'No content'}

Requirements:
- Maximum {max_length} characters each
- Include primary keywords at the beginning
- Unique and descriptive
- No keyword stuffing
- Language: {language}

Provide {count} title options, one per line:"""

        config = LLMConfig(
            model=self.model or self._get_default_model(),
            temperature=0.8,  # Higher temperature for variety
            max_tokens=200,
        )

        response = await self.llm.generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt,
            config=config,
        )

        # Parse titles from response
        titles = []
        for line in response.strip().split("\n"):
            line = line.strip().strip("123456789.-) ")
            if line and len(line) > 10:  # Filter out empty/short lines
                if len(line) > max_length:
                    line = line[:max_length - 3] + "..."
                titles.append(line)

        return titles[:count]

    async def generate_h1_suggestion(
        self,
        page: Page,
        language: str = "en",
    ) -> str:
        """
        Generate an optimized H1 heading.

        Args:
            page: Page object
            language: Content language

        Returns:
            Suggested H1 heading
        """
        system_prompt = self._get_system_prompt(language)

        user_prompt = f"""Generate an SEO-optimized H1 heading for this webpage.

URL: {page.url}
Title: {page.title or 'N/A'}
Current H1: {page.h1 or 'N/A'}

Content excerpt:
{page.text_content[:500] if page.text_content else 'No content'}

Requirements:
- Clear and descriptive
- Include primary keyword
- 40-70 characters
- Engaging and relevant
- Language: {language}

H1 heading:"""

        config = LLMConfig(
            model=self.model or self._get_default_model(),
            temperature=0.7,
            max_tokens=50,
        )

        h1 = await self.llm.generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt,
            config=config,
        )

        return h1.strip().strip('"\'#')

    async def generate_content_recommendations(
        self,
        page: Page,
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Generate comprehensive content improvement recommendations.

        Args:
            page: Page object
            language: Content language

        Returns:
            Dictionary with recommendations
        """
        system_prompt = self._get_system_prompt(language)

        user_prompt = f"""Analyze this webpage and provide SEO improvement recommendations.

URL: {page.url}
Title: {page.title or 'N/A'}
Meta Description: {page.meta_description or 'N/A'}
H1: {page.h1 or 'N/A'}
Word Count: {page.word_count}
Language: {page.lang or language}

Content excerpt:
{page.text_content[:1000] if page.text_content else 'No content'}

Provide recommendations for:
1. Content quality and depth
2. Keyword optimization
3. Structure and headings
4. Readability improvements
5. Missing elements

Format as JSON with keys: content_quality, keywords, structure, readability, missing_elements"""

        config = LLMConfig(
            model=self.model or self._get_default_model(),
            temperature=0.5,  # Lower temperature for consistent analysis
            max_tokens=500,
        )

        response = await self.llm.generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt,
            config=config,
        )

        # Try to parse as JSON, fallback to text
        import json
        try:
            recommendations = json.loads(response)
        except json.JSONDecodeError:
            recommendations = {
                "analysis": response,
                "format": "text",
            }

        return recommendations

    def _get_system_prompt(self, language: str) -> str:
        """
        Get system prompt for the LLM.

        Args:
            language: Content language

        Returns:
            System prompt text
        """
        if language == "fr":
            return (
                "Vous êtes un expert SEO spécialisé dans la création de contenu optimisé pour les moteurs de recherche. "
                "Vos suggestions sont concises, pertinentes et suivent les meilleures pratiques SEO actuelles. "
                "Vous écrivez en français naturel et évitez le bourrage de mots-clés."
            )
        else:
            return (
                "You are an SEO expert specialized in creating search engine optimized content. "
                "Your suggestions are concise, relevant, and follow current SEO best practices. "
                "You write in natural English and avoid keyword stuffing."
            )

    def _get_default_model(self) -> str:
        """
        Get default model for the provider.

        Returns:
            Model name
        """
        if self.provider == "openai":
            return "gpt-3.5-turbo-1106"
        elif self.provider == "anthropic":
            return "claude-3-sonnet-20240229"
        elif self.provider == "huggingface":
            return "mistralai/Mistral-7B-Instruct-v0.2"
        else:
            return "gpt-3.5-turbo-1106"  # Fallback
