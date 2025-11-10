"""Site tree/architecture generation service."""

import json
import re
from typing import Optional, Dict, Any, List
from app.services.llm import LLMFactory, LLMConfig


class SiteTreeGenerator:
    """
    Service for generating SEO-optimized site architectures.

    Uses LLMs to create hierarchical site structures based on:
    - Primary keywords
    - Business theme/niche
    - Target depth
    - SEO best practices

    Output includes:
    - Page titles and slugs
    - URL structure
    - Meta descriptions
    - Content briefs
    - Internal linking suggestions
    """

    def __init__(
        self,
        provider: str = "openai",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize site tree generator.

        Args:
            provider: LLM provider ("openai", "anthropic", "huggingface")
            api_key: API key for the provider
            model: Optional specific model to use
        """
        if not api_key:
            raise ValueError("API key is required for site tree generation")

        self.llm = LLMFactory.create(provider=provider, api_key=api_key)
        self.provider = provider
        self.model = model

    async def generate_tree(
        self,
        keyword: str,
        theme: Optional[str] = None,
        depth: int = 3,
        max_nodes_per_level: int = 7,
        language: str = "en",
        business_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a complete site architecture tree.

        Args:
            keyword: Primary keyword/topic for the site
            theme: Business theme or niche
            depth: Maximum tree depth (1-5)
            max_nodes_per_level: Maximum children per node (default: 7)
            language: Content language
            business_type: Type of business (ecommerce, blog, saas, etc.)

        Returns:
            Dictionary with hierarchical tree structure
        """
        # Validate inputs
        if depth < 1 or depth > 5:
            raise ValueError("Depth must be between 1 and 5")

        if max_nodes_per_level < 3 or max_nodes_per_level > 15:
            raise ValueError("max_nodes_per_level must be between 3 and 15")

        # Build prompt
        system_prompt = self._get_system_prompt(language)
        user_prompt = self._build_generation_prompt(
            keyword=keyword,
            theme=theme,
            depth=depth,
            max_nodes_per_level=max_nodes_per_level,
            business_type=business_type,
            language=language,
        )

        config = LLMConfig(
            model=self.model or self._get_default_model(),
            temperature=0.7,
            max_tokens=2000,
        )

        # Generate tree
        response = await self.llm.generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt,
            config=config,
        )

        # Parse and structure response
        try:
            tree_data = self._parse_tree_response(response)
        except Exception as e:
            # Fallback: try to extract JSON from response
            tree_data = self._extract_json_from_response(response)

        # Enrich tree with SEO metadata
        enriched_tree = await self._enrich_tree_nodes(tree_data, keyword, language)

        return enriched_tree

    def _build_generation_prompt(
        self,
        keyword: str,
        theme: Optional[str],
        depth: int,
        max_nodes_per_level: int,
        business_type: Optional[str],
        language: str,
    ) -> str:
        """Build the LLM prompt for tree generation."""
        business_context = f" for a {business_type} business" if business_type else ""
        theme_context = f" with theme '{theme}'" if theme else ""

        prompt = f"""Generate a comprehensive site architecture{business_context}{theme_context}.

Primary Keyword: {keyword}
Target Depth: {depth} levels
Max Children per Node: {max_nodes_per_level}
Language: {language}

Requirements:
1. Create a hierarchical structure with {depth} levels maximum
2. Each parent should have 3-{max_nodes_per_level} children
3. Focus on SEO-friendly structure and information architecture
4. Use keyword variations and semantic relationships
5. Follow logical categorization and user intent
6. Create clear, descriptive slugs (lowercase, hyphens)

Output Format (JSON):
{{
  "name": "Homepage",
  "slug": "/",
  "keyword": "primary keyword",
  "title": "SEO-optimized page title",
  "meta_description": "Compelling meta description (150-160 chars)",
  "priority": "critical",
  "children": [
    {{
      "name": "Category 1",
      "slug": "/category-1",
      "keyword": "category keyword",
      "title": "Category 1 Title",
      "meta_description": "Category description",
      "priority": "high",
      "children": [...]
    }}
  ]
}}

Generate the complete site tree as JSON:"""

        return prompt

    def _parse_tree_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response into tree structure.

        Args:
            response: LLM response text

        Returns:
            Parsed tree dictionary
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
                raise ValueError("No valid JSON found in response")

        tree_data = json.loads(json_str)
        return tree_data

    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Fallback method to extract JSON from response."""
        try:
            # Find first { and last }
            start = response.find("{")
            end = response.rfind("}") + 1

            if start == -1 or end == 0:
                raise ValueError("No JSON object found")

            json_str = response[start:end]
            return json.loads(json_str)
        except Exception as e:
            raise ValueError(f"Failed to parse tree response: {e}")

    async def _enrich_tree_nodes(
        self,
        tree: Dict[str, Any],
        root_keyword: str,
        language: str,
        current_level: int = 0,
    ) -> Dict[str, Any]:
        """
        Enrich tree nodes with additional metadata.

        Args:
            tree: Tree dictionary
            root_keyword: Root keyword for context
            language: Content language
            current_level: Current depth level

        Returns:
            Enriched tree
        """
        # Add computed fields
        if "level" not in tree:
            tree["level"] = current_level

        if "url" not in tree and "slug" in tree:
            tree["url"] = tree["slug"]

        # Set default priority
        if "priority" not in tree:
            if current_level == 0:
                tree["priority"] = "critical"
            elif current_level == 1:
                tree["priority"] = "high"
            else:
                tree["priority"] = "medium"

        # Set default word count target
        if "target_word_count" not in tree:
            if current_level == 0:
                tree["target_word_count"] = 1500
            elif current_level == 1:
                tree["target_word_count"] = 1200
            else:
                tree["target_word_count"] = 800

        # Ensure required fields
        if "name" not in tree:
            tree["name"] = tree.get("title", "Untitled")

        if "slug" not in tree:
            tree["slug"] = self._generate_slug(tree["name"])

        if "keyword" not in tree:
            tree["keyword"] = root_keyword

        # Recursively enrich children
        if "children" in tree and isinstance(tree["children"], list):
            tree["children"] = [
                await self._enrich_tree_nodes(child, root_keyword, language, current_level + 1)
                for child in tree["children"]
            ]

        return tree

    def _generate_slug(self, text: str) -> str:
        """
        Generate URL-friendly slug from text.

        Args:
            text: Input text

        Returns:
            URL slug
        """
        # Convert to lowercase
        slug = text.lower()

        # Replace spaces and special chars with hyphens
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[-\s]+", "-", slug)

        # Remove leading/trailing hyphens
        slug = slug.strip("-")

        return slug

    def flatten_tree(self, tree: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Flatten tree structure into a list of nodes.

        Args:
            tree: Hierarchical tree dictionary

        Returns:
            List of all nodes with parent references
        """
        nodes = []

        def traverse(node: Dict[str, Any], parent_slug: Optional[str] = None):
            node_copy = node.copy()
            children = node_copy.pop("children", [])

            node_copy["parent_slug"] = parent_slug
            nodes.append(node_copy)

            for child in children:
                traverse(child, node_copy["slug"])

        traverse(tree)
        return nodes

    def _get_system_prompt(self, language: str) -> str:
        """Get system prompt for the LLM."""
        if language == "fr":
            return (
                "Vous êtes un expert en architecture de l'information et SEO. "
                "Vous créez des structures de site web logiques, optimisées pour les moteurs de recherche "
                "et l'expérience utilisateur. Vos suggestions suivent les meilleures pratiques SEO : "
                "hiérarchie claire, slugs descriptifs, distribution de mots-clés, et navigation intuitive."
            )
        else:
            return (
                "You are an information architecture and SEO expert. "
                "You create logical, SEO-optimized website structures that enhance user experience "
                "and search engine visibility. Your suggestions follow SEO best practices: "
                "clear hierarchy, descriptive slugs, keyword distribution, and intuitive navigation."
            )

    def _get_default_model(self) -> str:
        """Get default model for the provider."""
        if self.provider == "openai":
            return "gpt-4-turbo-preview"
        elif self.provider == "anthropic":
            return "claude-3-sonnet-20240229"
        elif self.provider == "huggingface":
            return "mistralai/Mistral-7B-Instruct-v0.2"
        else:
            return "gpt-4-turbo-preview"
