"""SEO content generator service."""

import json
import re
from typing import Dict, Any, List, Optional
from app.services.content_templates import (
    content_template_service,
    PageType,
    ContentTone
)
from app.services.llm_adapter import llm_adapter


class SEOContentGenerator:
    """
    Service for generating SEO-optimized content using LLM.

    Uses templates and best practices to create high-quality,
    search-engine-friendly content.
    """

    async def generate_content(
        self,
        keyword: str,
        page_type: str,
        tone: str = "professional",
        length: int = 1000,
        language: str = "en",
        context: str = None,
        competitor_urls: List[str] = None,
        provider: str = "openai"
    ) -> Dict[str, Any]:
        """
        Generate SEO-optimized content.

        Args:
            keyword: Target keyword
            page_type: Type of page (homepage, article, product, etc.)
            tone: Content tone (professional, casual, etc.)
            length: Target word count
            language: Content language
            context: Additional context or requirements
            competitor_urls: List of competitor URLs for analysis
            provider: LLM provider

        Returns:
            Generated content with structure and metadata
        """
        # Convert string to enum
        try:
            page_type_enum = PageType(page_type)
            tone_enum = ContentTone(tone)
        except ValueError as e:
            raise ValueError(f"Invalid page_type or tone: {e}")

        # Get content structure
        structure = content_template_service.get_structure(page_type_enum)

        # Adjust length to stay within bounds
        length = max(structure.min_words, min(structure.max_words, length))

        # Analyze competitors if URLs provided (simplified version)
        competitor_content = []
        if competitor_urls:
            competitor_content = await self._analyze_competitors(competitor_urls)

        # Build prompt
        system_prompt = content_template_service.get_system_prompt(language)
        user_prompt = content_template_service.build_generation_prompt(
            page_type=page_type_enum,
            keyword=keyword,
            tone=tone_enum,
            length=length,
            language=language,
            context=context,
            competitor_content=competitor_content
        )

        print(f"[ContentGen] Generating {page_type} content for keyword '{keyword}'...")

        # Generate with LLM
        response = await llm_adapter.generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt,
            provider=provider,
            max_tokens=3000,
            temperature=0.7
        )

        print(f"[ContentGen] LLM response received, parsing...")

        # Parse JSON response
        content_data = self._parse_content_response(response)

        # Validate and enrich
        content_data = self._enrich_content(content_data, keyword, page_type, structure)

        print(f"[ContentGen] Content generated successfully ({content_data.get('word_count', 0)} words)")

        return content_data

    async def optimize_content(
        self,
        content: str,
        keyword: str,
        page_type: str,
        language: str = "en",
        provider: str = "openai"
    ) -> Dict[str, Any]:
        """
        Optimize existing content for SEO.

        Args:
            content: Existing content to optimize
            keyword: Target keyword
            page_type: Type of page
            language: Content language
            provider: LLM provider

        Returns:
            Optimized content and suggestions
        """
        try:
            page_type_enum = PageType(page_type)
        except ValueError as e:
            raise ValueError(f"Invalid page_type: {e}")

        structure = content_template_service.get_structure(page_type_enum)

        system_prompt = content_template_service.get_system_prompt(language)

        lang_instruction = (
            "Répondez en français." if language == "fr"
            else "Respond in English."
        )

        user_prompt = f"""Optimize this content for SEO while preserving its core message.

**Target Keyword**: {keyword}
**Page Type**: {page_type}
**Language**: {language}

**Current Content**:
{content}

**Optimization Tasks**:
1. Ensure keyword "{keyword}" appears naturally 3-5 times
2. Improve heading structure (H2/H3) for better readability
3. Add semantic variations and LSI keywords
4. Enhance meta title and description
5. Improve readability (short paragraphs, transitions)
6. Add or improve call-to-action if applicable
7. Suggest FAQ questions if applicable

{lang_instruction}

**Output Format** (JSON):
{{
  "optimized_content": "Full optimized content...",
  "improvements": [
    "Improvement 1",
    "Improvement 2"
  ],
  "seo_score": 85,
  "keyword_density": 2.5,
  "readability_score": "good",
  "suggestions": [
    "Suggestion 1",
    "Suggestion 2"
  ],
  "meta_title": "Optimized meta title",
  "meta_description": "Optimized meta description"
}}

Generate the optimization as JSON:"""

        response = await llm_adapter.generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt,
            provider=provider,
            max_tokens=3000,
            temperature=0.6
        )

        # Parse response
        optimization_data = self._parse_json_response(response)

        return optimization_data

    async def _analyze_competitors(self, urls: List[str]) -> List[str]:
        """
        Analyze competitor content (simplified).

        In a full implementation, this would scrape and analyze competitor pages.
        For now, it's a placeholder.

        Args:
            urls: List of competitor URLs

        Returns:
            List of content snippets
        """
        # TODO: Implement actual web scraping
        # For now, return empty list
        # Could use BeautifulSoup + requests/httpx to scrape competitor content
        return []

    def _parse_content_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response to extract JSON content."""
        return self._parse_json_response(response)

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response.

        Args:
            response: LLM response text

        Returns:
            Parsed JSON dictionary
        """
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON directly
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("No valid JSON found in LLM response")

        try:
            data = json.loads(json_str)
            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON: {e}")

    def _enrich_content(
        self,
        content_data: Dict[str, Any],
        keyword: str,
        page_type: str,
        structure: Any
    ) -> Dict[str, Any]:
        """
        Enrich content data with additional metadata.

        Args:
            content_data: Parsed content data
            keyword: Target keyword
            page_type: Page type
            structure: Content structure

        Returns:
            Enriched content data
        """
        # Add metadata
        content_data["target_keyword"] = keyword
        content_data["page_type"] = page_type

        # Calculate actual word count if not provided
        if "word_count" not in content_data or not content_data["word_count"]:
            full_text = self._extract_full_text(content_data)
            content_data["word_count"] = len(full_text.split())

        # Add structure info
        content_data["structure"] = {
            "min_words": structure.min_words,
            "max_words": structure.max_words,
            "target_h2_count": structure.h2_count,
            "target_h3_count": structure.h3_count
        }

        return content_data

    def _extract_full_text(self, content_data: Dict[str, Any]) -> str:
        """Extract all text content for word counting."""
        text_parts = []

        if "title" in content_data:
            text_parts.append(content_data["title"])

        if "introduction" in content_data:
            text_parts.append(content_data["introduction"])

        if "sections" in content_data:
            for section in content_data["sections"]:
                if "heading" in section:
                    text_parts.append(section["heading"])
                if "content" in section:
                    text_parts.append(section["content"])

        if "conclusion" in content_data:
            text_parts.append(content_data["conclusion"])

        return " ".join(text_parts)


# Singleton instance
seo_content_generator = SEOContentGenerator()
