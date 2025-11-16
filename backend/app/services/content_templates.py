"""Content templates for SEO content generation."""

from enum import Enum
from typing import Dict, Any, List
from dataclasses import dataclass


class PageType(Enum):
    """Types of pages for content generation."""
    HOMEPAGE = "homepage"
    CATEGORY = "category"
    PRODUCT = "product"
    ARTICLE = "article"
    LANDING_PAGE = "landing_page"
    SERVICE = "service"
    ABOUT = "about"
    FAQ = "faq"


class ContentTone(Enum):
    """Content tone options."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    EXPERT = "expert"
    PERSUASIVE = "persuasive"
    INFORMATIVE = "informative"


@dataclass
class ContentStructure:
    """Structure definition for a content type."""
    sections: List[str]
    min_words: int
    max_words: int
    include_cta: bool
    include_faq: bool
    h2_count: int
    h3_count: int


class ContentTemplateService:
    """
    Service for managing content templates and structures.

    Provides templates for different page types with SEO best practices.
    """

    # Content structures by page type
    STRUCTURES: Dict[PageType, ContentStructure] = {
        PageType.HOMEPAGE: ContentStructure(
            sections=[
                "hero_section",
                "introduction",
                "key_benefits",
                "how_it_works",
                "social_proof",
                "cta"
            ],
            min_words=300,
            max_words=800,
            include_cta=True,
            include_faq=False,
            h2_count=3,
            h3_count=6
        ),
        PageType.CATEGORY: ContentStructure(
            sections=[
                "introduction",
                "category_overview",
                "benefits",
                "key_features",
                "buying_guide",
                "conclusion"
            ],
            min_words=500,
            max_words=1200,
            include_cta=True,
            include_faq=True,
            h2_count=4,
            h3_count=8
        ),
        PageType.PRODUCT: ContentStructure(
            sections=[
                "product_introduction",
                "key_features",
                "specifications",
                "benefits",
                "use_cases",
                "conclusion",
                "cta"
            ],
            min_words=600,
            max_words=1500,
            include_cta=True,
            include_faq=True,
            h2_count=5,
            h3_count=10
        ),
        PageType.ARTICLE: ContentStructure(
            sections=[
                "introduction",
                "context",
                "main_content",
                "examples",
                "best_practices",
                "conclusion"
            ],
            min_words=1000,
            max_words=2500,
            include_cta=True,
            include_faq=False,
            h2_count=6,
            h3_count=12
        ),
        PageType.LANDING_PAGE: ContentStructure(
            sections=[
                "headline",
                "problem",
                "solution",
                "features",
                "benefits",
                "social_proof",
                "guarantee",
                "cta"
            ],
            min_words=400,
            max_words=1000,
            include_cta=True,
            include_faq=True,
            h2_count=5,
            h3_count=8
        ),
        PageType.SERVICE: ContentStructure(
            sections=[
                "service_introduction",
                "what_we_offer",
                "process",
                "benefits",
                "pricing_info",
                "cta"
            ],
            min_words=500,
            max_words=1200,
            include_cta=True,
            include_faq=True,
            h2_count=4,
            h3_count=8
        ),
        PageType.ABOUT: ContentStructure(
            sections=[
                "company_story",
                "mission_vision",
                "team",
                "values",
                "achievements"
            ],
            min_words=400,
            max_words=900,
            include_cta=False,
            include_faq=False,
            h2_count=4,
            h3_count=6
        ),
        PageType.FAQ: ContentStructure(
            sections=[
                "introduction",
                "questions_answers",
                "contact_cta"
            ],
            min_words=600,
            max_words=1500,
            include_cta=True,
            include_faq=False,  # Already is FAQ
            h2_count=8,
            h3_count=0
        ),
    }

    def get_structure(self, page_type: PageType) -> ContentStructure:
        """Get content structure for a page type."""
        return self.STRUCTURES.get(page_type)

    def get_system_prompt(self, language: str = "en") -> str:
        """Get system prompt for content generation."""
        if language == "fr":
            return (
                "Vous êtes un expert en rédaction SEO et marketing de contenu. "
                "Vous créez des contenus optimisés pour les moteurs de recherche "
                "tout en restant engageants et utiles pour les utilisateurs. "
                "Vous suivez les meilleures pratiques SEO : utilisation naturelle de mots-clés, "
                "structure claire avec titres hiérarchisés, contenu de qualité, et appels à l'action pertinents."
            )
        else:
            return (
                "You are an expert SEO content writer and marketing specialist. "
                "You create content optimized for search engines while remaining "
                "engaging and valuable for users. You follow SEO best practices: "
                "natural keyword usage, clear hierarchical structure, quality content, "
                "and relevant calls-to-action."
            )

    def build_generation_prompt(
        self,
        page_type: PageType,
        keyword: str,
        tone: ContentTone,
        length: int,
        language: str,
        context: str = None,
        competitor_content: List[str] = None
    ) -> str:
        """
        Build content generation prompt.

        Args:
            page_type: Type of page
            keyword: Target keyword
            tone: Content tone
            length: Target word count
            language: Content language
            context: Additional context
            competitor_content: List of competitor content for inspiration

        Returns:
            Complete prompt for LLM
        """
        structure = self.get_structure(page_type)

        # Build sections description
        sections_text = "\n".join([f"- {section}" for section in structure.sections])

        # Add competitor analysis if available
        competitor_text = ""
        if competitor_content and len(competitor_content) > 0:
            competitor_text = "\n\nCompetitor content analysis (for inspiration, DO NOT copy):\n"
            for i, content in enumerate(competitor_content[:3], 1):
                competitor_text += f"\nCompetitor {i} (first 500 chars): {content[:500]}...\n"

        # Context text
        context_text = f"\n\nAdditional context: {context}" if context else ""

        # Language instruction
        lang_instruction = (
            "Rédigez le contenu en français." if language == "fr"
            else "Write the content in English."
        )

        prompt = f"""Generate SEO-optimized content for a {page_type.value} page.

**Target Keyword**: {keyword}
**Content Type**: {page_type.value}
**Tone**: {tone.value}
**Target Length**: ~{length} words (min: {structure.min_words}, max: {structure.max_words})
**Language**: {language}

**Required Structure**:
{sections_text}

**SEO Requirements**:
1. Use the target keyword "{keyword}" naturally 3-5 times in the content
2. Include the keyword in the H1 title
3. Use semantic variations and LSI keywords
4. Create {structure.h2_count} H2 headings and {structure.h3_count} H3 headings
5. Write engaging meta title (50-60 chars) and meta description (150-160 chars)
6. Ensure content is readable (use short paragraphs, bullet points, etc.)
{"7. Include a clear call-to-action" if structure.include_cta else ""}
{"8. Add a FAQ section with 5-7 questions" if structure.include_faq else ""}

**Content Guidelines**:
- Write original, high-quality content
- Focus on user intent and value
- Use active voice and clear language
- Include relevant examples and details
- Make it engaging and scannable{competitor_text}{context_text}

{lang_instruction}

**Output Format** (JSON):
{{
  "title": "SEO-optimized H1 title with keyword",
  "meta_title": "Meta title (50-60 chars)",
  "meta_description": "Meta description (150-160 chars)",
  "introduction": "Opening paragraph with hook and keyword",
  "sections": [
    {{
      "heading": "H2 heading",
      "subheadings": ["H3 subheading 1", "H3 subheading 2"],
      "content": "Section content..."
    }}
  ],
  "conclusion": "Closing paragraph",
  "cta": "Call-to-action text" {"or null" if not structure.include_cta else ""},
  "faq": [
    {{"question": "Q1?", "answer": "A1"}}
  ] {"or []" if not structure.include_faq else ""},
  "keywords_used": ["keyword1", "keyword2"],
  "word_count": 1234
}}

Generate the complete content as JSON:"""

        return prompt

    def get_available_page_types(self) -> List[Dict[str, str]]:
        """Get list of available page types."""
        return [
            {
                "value": pt.value,
                "label": pt.value.replace("_", " ").title(),
                "description": self._get_page_type_description(pt)
            }
            for pt in PageType
        ]

    def get_available_tones(self) -> List[Dict[str, str]]:
        """Get list of available content tones."""
        return [
            {
                "value": tone.value,
                "label": tone.value.title()
            }
            for tone in ContentTone
        ]

    def _get_page_type_description(self, page_type: PageType) -> str:
        """Get description for a page type."""
        descriptions = {
            PageType.HOMEPAGE: "Main landing page of the website",
            PageType.CATEGORY: "Category or collection page",
            PageType.PRODUCT: "Individual product or service page",
            PageType.ARTICLE: "Blog post or informational article",
            PageType.LANDING_PAGE: "Conversion-focused landing page",
            PageType.SERVICE: "Service description page",
            PageType.ABOUT: "About us or company page",
            PageType.FAQ: "Frequently asked questions page"
        }
        return descriptions.get(page_type, "")


# Singleton instance
content_template_service = ContentTemplateService()
