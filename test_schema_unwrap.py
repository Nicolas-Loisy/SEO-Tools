#!/usr/bin/env python3
"""Test script to verify schema unwrapping logic."""

import json

def unwrap_nested_schema(schema: dict) -> dict:
    """
    Unwrap incorrectly nested schema objects.

    Sometimes schemas get wrapped in extra "schema" keys.
    This function unwraps them to get the actual JSON-LD schema.
    """
    # If schema has a single "schema" key that contains the actual schema
    if 'schema' in schema and '@context' not in schema and '@type' not in schema:
        # Recursively unwrap in case of multiple levels
        return unwrap_nested_schema(schema['schema'])

    return schema


def test_unwrap():
    """Test the unwrap function with various cases."""

    print("=" * 60)
    print("Testing Schema Unwrap Function")
    print("=" * 60)

    # Test 1: Correct schema (no unwrapping needed)
    print("\n✓ Test 1: Already correct schema")
    correct = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "Test Article"
    }
    result = unwrap_nested_schema(correct)
    assert result == correct
    assert '@context' in result and '@type' in result
    print(f"  Input keys: {list(correct.keys())}")
    print(f"  Output keys: {list(result.keys())}")
    print(f"  ✓ Passed - Schema unchanged")

    # Test 2: Single level nesting
    print("\n✓ Test 2: Single level 'schema' nesting")
    single_nested = {
        "schema": {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "Test Product"
        }
    }
    result = unwrap_nested_schema(single_nested)
    assert '@context' in result
    assert '@type' in result
    assert result['@type'] == 'Product'
    assert 'schema' not in result
    print(f"  Input has 'schema' key: {'schema' in single_nested}")
    print(f"  Output has '@type': {'@type' in result}")
    print(f"  Output @type: {result['@type']}")
    print(f"  ✓ Passed - Schema unwrapped once")

    # Test 3: Multiple levels of nesting (the bug scenario)
    print("\n✓ Test 3: Multiple nested 'schema' levels (THE BUG)")
    multi_nested = {
        "schema": {
            "schema": {
                "schema": {
                    "@context": "https://schema.org",
                    "@type": "Article",
                    "headline": "Deeply Nested"
                }
            }
        }
    }
    result = unwrap_nested_schema(multi_nested)
    assert '@context' in result
    assert '@type' in result
    assert result['headline'] == 'Deeply Nested'
    assert 'schema' not in result
    print(f"  Input depth: 3 levels of 'schema'")
    print(f"  Output has '@type': {'@type' in result}")
    print(f"  Output headline: {result.get('headline')}")
    print(f"  ✓ Passed - All nested levels unwrapped")

    # Test 4: Schema with actual "schema" property (should NOT unwrap)
    print("\n✓ Test 4: Schema with legitimate 'schema' property")
    legitimate = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": "Test",
        "schema": "https://example.com/schema.json"  # This is a property value
    }
    result = unwrap_nested_schema(legitimate)
    assert result == legitimate
    assert '@context' in result
    assert result['schema'] == "https://example.com/schema.json"
    print(f"  Input has @context: {'@context' in legitimate}")
    print(f"  Output unchanged: {result == legitimate}")
    print(f"  ✓ Passed - Legitimate 'schema' property preserved")

    # Test 5: Complex enhancement response structure
    print("\n✓ Test 5: Full enhancement response (as from API)")
    api_response = {
        "page_id": 123,
        "enhanced_schema": {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": "Enhanced Article"
        },
        "improvements": ["Added author", "Added datePublished"],
        "recommendations": ["Add images", "Add video"]
    }
    # This should NOT be unwrapped (it's not nested incorrectly)
    schema_part = api_response["enhanced_schema"]
    result = unwrap_nested_schema(schema_part)
    assert '@context' in result
    assert result['headline'] == "Enhanced Article"
    print(f"  Schema from API response")
    print(f"  Output has @type: {'@type' in result}")
    print(f"  ✓ Passed - API response structure handled correctly")

    print("\n" + "=" * 60)
    print("All tests passed! ✅")
    print("=" * 60)
    print("\nSummary:")
    print("- Correct schemas remain unchanged")
    print("- Single nesting is unwrapped")
    print("- Multiple nesting levels are fully unwrapped")
    print("- Legitimate 'schema' properties are preserved")
    print("- API response structures work correctly")


if __name__ == "__main__":
    test_unwrap()
