"""LLM-based Schema.org enhancement service."""

from typing import Dict, Any, Optional
import json

from app.models.page import Page
from app.services.llm_adapter import LLMAdapter


class SchemaEnhancer:
    """Service for enhancing JSON-LD schemas using LLM."""

    def __init__(self):
        """Initialize enhancer with LLM adapter."""
        self.llm_adapter = LLMAdapter()

    async def enhance_schema(
        self,
        page: Page,
        base_schema: Dict[str, Any],
        provider: str = "openai"
    ) -> Dict[str, Any]:
        """
        Enhance a JSON-LD schema using LLM.

        Args:
            page: Page model instance
            base_schema: Base JSON-LD schema to enhance
            provider: LLM provider to use

        Returns:
            Enhanced JSON-LD schema
        """
        # Unwrap any nested "schema" keys in input
        base_schema = self._unwrap_nested_schema(base_schema)

        # Build prompt for LLM
        prompt = self._build_enhancement_prompt(page, base_schema)

        try:
            # Call LLM
            response = await self.llm_adapter.generate(
                prompt=prompt,
                provider=provider,
                max_tokens=2000,
                temperature=0.3  # Low temperature for consistent output
            )

            # Parse JSON response
            enhanced_schema = self._parse_llm_response(response, base_schema)

            return enhanced_schema

        except Exception as e:
            # If LLM fails, return base schema
            print(f"Schema enhancement failed: {e}")
            return base_schema

    def _build_enhancement_prompt(
        self,
        page: Page,
        base_schema: Dict[str, Any]
    ) -> str:
        """Build prompt for LLM enhancement."""
        schema_type = base_schema.get("@type", "Article")

        prompt = f"""You are an SEO expert specializing in Schema.org structured data.

Your task is to enhance the following JSON-LD schema to make it more complete and SEO-optimized.

**Page Information:**
- URL: {page.url}
- Title: {page.title or 'N/A'}
- Meta Description: {page.meta_description or 'N/A'}
- Content Preview: {(page.text_content or '')[:500]}...

**Current Schema ({schema_type}):**
```json
{json.dumps(base_schema, indent=2)}
```

**Enhancement Instructions:**
1. Analyze the page content and improve the schema
2. Add missing recommended fields for {schema_type}
3. Improve descriptions to be more SEO-friendly
4. Extract additional metadata if present in the content
5. Ensure all URLs are absolute
6. Follow Google's structured data guidelines

**Important:**
- Return ONLY valid JSON
- Keep the same @type ({schema_type})
- Don't invent data - only use what's in the page content
- Preserve all existing fields
- Add fields that improve SEO value

Return the enhanced JSON-LD schema:"""

        return prompt

    def _parse_llm_response(
        self,
        response: str,
        fallback_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse and validate LLM response for simple schema enhancement."""
        try:
            # Try to extract JSON from response
            # LLM might wrap it in ```json``` code blocks
            response = response.strip()

            # Remove code block markers if present
            if response.startswith('```json'):
                response = response[7:]
            if response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]

            response = response.strip()

            # Parse JSON
            enhanced_schema = json.loads(response)

            # Validate that it's still a proper schema
            if '@context' not in enhanced_schema:
                enhanced_schema['@context'] = 'https://schema.org'

            if '@type' not in enhanced_schema:
                return fallback_schema

            return enhanced_schema

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Failed to parse LLM response: {e}")
            return fallback_schema

    def _unwrap_nested_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unwrap incorrectly nested schema objects.

        Sometimes schemas get wrapped in extra "schema" keys.
        This function unwraps them to get the actual JSON-LD schema.
        """
        # If schema has a single "schema" key that contains the actual schema
        if 'schema' in schema and '@context' not in schema and '@type' not in schema:
            # Recursively unwrap in case of multiple levels
            return self._unwrap_nested_schema(schema['schema'])

        return schema

    def _parse_enhancement_response(
        self,
        response: str,
        fallback_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Parse and validate LLM response for enhancement with suggestions.

        Expects response in format:
        {
            "enhanced_schema": {...},
            "improvements": [...],
            "recommendations": [...]
        }
        """
        try:
            # Try to extract JSON from response
            response = response.strip()

            # Remove code block markers if present
            if response.startswith('```json'):
                response = response[7:]
            if response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]

            response = response.strip()

            # Parse JSON
            result = json.loads(response)
            print(f"[Parser] Parsed JSON successfully, top-level keys: {list(result.keys())}")

            # Validate structure
            if not isinstance(result, dict):
                print(f"[Parser] Result is not a dict, using fallback")
                return fallback_result

            # Extract enhanced_schema
            enhanced_schema = result.get('enhanced_schema', {})
            print(f"[Parser] Extracted enhanced_schema, keys: {list(enhanced_schema.keys()) if isinstance(enhanced_schema, dict) else 'NOT A DICT'}")

            # Ensure enhanced_schema is valid
            if not isinstance(enhanced_schema, dict):
                print(f"[Parser] enhanced_schema is not a dict, using fallback")
                enhanced_schema = fallback_result.get('enhanced_schema', {})

            # Check for nested "schema" before unwrapping
            has_nested_schema = 'schema' in enhanced_schema and '@context' not in enhanced_schema
            if has_nested_schema:
                print(f"[Parser] WARNING: Found nested 'schema' key, unwrapping...")

            # Unwrap any nested "schema" keys
            enhanced_schema = self._unwrap_nested_schema(enhanced_schema)

            if has_nested_schema:
                print(f"[Parser] After unwrap, keys: {list(enhanced_schema.keys())[:5]}")

            # Validate it's a proper JSON-LD schema
            if '@context' not in enhanced_schema:
                print(f"[Parser] Missing @context, adding default")
                enhanced_schema['@context'] = 'https://schema.org'

            # If @type is missing, use fallback
            if '@type' not in enhanced_schema:
                print(f"[Parser] Missing @type, using fallback schema")
                enhanced_schema = fallback_result.get('enhanced_schema', {})

            # Build clean result
            return {
                'enhanced_schema': enhanced_schema,
                'improvements': result.get('improvements', []) if isinstance(result.get('improvements'), list) else [],
                'recommendations': result.get('recommendations', []) if isinstance(result.get('recommendations'), list) else []
            }

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"[Parser] Failed to parse enhancement response: {type(e).__name__}: {e}")
            print(f"[Parser] Response preview: {response[:300]}...")
            return fallback_result

    async def enhance_with_suggestions(
        self,
        page: Page,
        base_schema: Dict[str, Any],
        provider: str = "openai"
    ) -> Dict[str, Any]:
        """
        Enhance schema and provide improvement suggestions.

        Returns both enhanced schema and human-readable suggestions.
        """
        # Unwrap any nested "schema" keys in input
        base_schema = self._unwrap_nested_schema(base_schema)

        schema_type = base_schema.get("@type", "Article")

        prompt = f"""You are an SEO expert specializing in Schema.org structured data.

Your task is to enhance the following JSON-LD schema and provide actionable recommendations.

**Page Information:**
- URL: {page.url}
- Title: {page.title or 'N/A'}
- Meta Description: {page.meta_description or 'N/A'}
- H1: {page.h1 or 'N/A'}
- Content Preview: {(page.text_content or '')[:500]}...

**Current Schema ({schema_type}):**
```json
{json.dumps(base_schema, indent=2)}
```

**Instructions:**
1. Analyze the page content and enhance the schema with relevant data
2. Add missing recommended fields for {schema_type} schema
3. Improve descriptions to be more SEO-friendly and informative
4. Extract additional metadata from the page content
5. Ensure all URLs are absolute and valid
6. Follow Google's structured data guidelines

**⚠️ CRITICAL - Response Format (READ CAREFULLY):**

You MUST respond with ONLY a valid JSON object. Here is an EXACT example of the correct format:

{{
  "enhanced_schema": {{
    "@context": "https://schema.org",
    "@type": "{schema_type}",
    "name": "Enhanced name here",
    "url": "https://example.com"
  }},
  "improvements": [
    "Added missing name field",
    "Enhanced description"
  ],
  "recommendations": [
    "Consider adding images",
    "Add author information"
  ]
}}

**⚠️ WRONG - DO NOT DO THIS:**
{{
  "enhanced_schema": {{
    "schema": {{
      "@context": "https://schema.org",
      ...
    }}
  }}
}}

**⚠️ WRONG - DO NOT DO THIS:**
{{
  "schema": {{
    "@context": "https://schema.org",
    ...
  }}
}}

**✅ CORRECT FORMAT:**
The "enhanced_schema" key must contain the Schema.org JSON-LD object DIRECTLY, starting immediately with "@context" and "@type" as the first properties. NO intermediate "schema" key or any other wrapper.

**Mandatory Rules:**
1. Return ONLY the JSON object, no explanatory text before or after
2. The "enhanced_schema" value starts directly with {{"@context": "https://schema.org", "@type": "{schema_type}", ...}}
3. Do NOT nest the schema under ANY additional keys like "schema", "data", "result", etc.
4. Do NOT invent data - only use information from the page content provided
5. Preserve all valuable existing fields from the current schema
"""

        try:
            response = await self.llm_adapter.generate(
                prompt=prompt,
                provider=provider,
                max_tokens=2500,
                temperature=0.3
            )

            # Log the raw response for debugging
            print(f"[SchemaEnhancer] Raw LLM response length: {len(response)}")
            print(f"[SchemaEnhancer] Response preview: {response[:200]}...")

            result = self._parse_enhancement_response(response, {
                "enhanced_schema": base_schema,
                "improvements": [],
                "recommendations": []
            })

            # Validate the result structure
            if 'enhanced_schema' in result:
                print(f"[SchemaEnhancer] Enhanced schema @type: {result['enhanced_schema'].get('@type', 'MISSING')}")
                print(f"[SchemaEnhancer] Enhanced schema keys: {list(result['enhanced_schema'].keys())[:5]}")

            return result

        except Exception as e:
            print(f"[SchemaEnhancer] Error during enhancement: {type(e).__name__}: {e}")
            return {
                "enhanced_schema": base_schema,
                "improvements": [],
                "recommendations": [],
                "error": str(e)
            }


# Singleton instance
schema_enhancer = SchemaEnhancer()
