# Content Generation with LLM

## Overview

SEO SaaS Tool integrates with multiple LLM providers to generate SEO-optimized content automatically. The system uses a Strategy pattern to support interchangeable backends.

## Supported Providers

### OpenAI (GPT-4, GPT-3.5)
- **Models**: gpt-4-turbo-preview, gpt-4, gpt-3.5-turbo
- **Best for**: High-quality content, complex analysis
- **Cost**: Medium to High
- **Speed**: Fast

### Anthropic (Claude)
- **Models**: claude-3-opus, claude-3-sonnet, claude-3-haiku
- **Best for**: Long-form content, detailed analysis
- **Cost**: Medium
- **Speed**: Fast

### HuggingFace (Open Source)
- **Models**: Mistral, Llama 2, Falcon
- **Best for**: Budget-friendly, privacy-focused
- **Cost**: Low (free tier available)
- **Speed**: Variable

## Features

### 1. Meta Description Generation

Generate compelling meta descriptions optimized for search engines.

```bash
curl -X POST http://localhost:8000/api/v1/content/meta-description \
  -H "X-API-Key: YOUR_KEY" \
  -d '{
    "page_id": 1,
    "max_length": 160,
    "provider": "openai"
  }'
```

Response:
```json
{
  "page_id": 1,
  "generated_description": "Discover comprehensive SEO tools to optimize your website. Improve rankings with advanced analytics, keyword research, and content optimization.",
  "original_description": null,
  "length": 153
}
```

### 2. Title Tag Suggestions

Get multiple SEO-optimized title options.

```bash
curl -X POST http://localhost:8000/api/v1/content/title-suggestions \
  -H "X-API-Key: YOUR_KEY" \
  -d '{
    "page_id": 1,
    "count": 3,
    "max_length": 60,
    "provider": "anthropic",
    "model": "claude-3-sonnet-20240229"
  }'
```

Response:
```json
{
  "page_id": 1,
  "suggestions": [
    "SEO Tools & Analytics Platform | Boost Your Rankings",
    "Complete SEO Solution - Keyword Research & Analysis",
    "Professional SEO Tools for Better Search Visibility"
  ],
  "original_title": "SEO Tools"
}
```

### 3. Content Recommendations

Get comprehensive SEO improvement recommendations.

```bash
curl -X POST http://localhost:8000/api/v1/content/recommendations \
  -H "X-API-Key: YOUR_KEY" \
  -d '{
    "page_id": 1,
    "provider": "openai"
  }'
```

Response:
```json
{
  "page_id": 1,
  "recommendations": {
    "content_quality": "Expand content to 1500+ words for better ranking",
    "keywords": "Add related keywords: 'search optimization', 'website analytics'",
    "structure": "Use H2/H3 headings to organize content",
    "readability": "Simplify complex sentences for better engagement",
    "missing_elements": "Add FAQ section, internal links, images with alt text"
  }
}
```

## Configuration

### Environment Variables

Add to `.env`:

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# HuggingFace
HUGGINGFACE_API_KEY=hf_...
```

### Provider Selection

Each endpoint accepts a `provider` parameter:
- `"openai"` - Use OpenAI GPT models
- `"anthropic"` - Use Anthropic Claude models
- `"huggingface"` - Use HuggingFace models

### Model Selection

Optionally specify exact model:

```json
{
  "provider": "openai",
  "model": "gpt-4-turbo-preview"
}
```

## Python Client Example

```python
import requests

API_KEY = "sk_test_..."
BASE_URL = "http://localhost:8000/api/v1"

def generate_meta_description(page_id: int, provider: str = "openai"):
    """Generate meta description for a page."""
    response = requests.post(
        f"{BASE_URL}/content/meta-description",
        headers={"X-API-Key": API_KEY},
        json={
            "page_id": page_id,
            "max_length": 160,
            "provider": provider,
        }
    )
    return response.json()

# Usage
result = generate_meta_description(page_id=1)
print(result["generated_description"])
```

## Cost Optimization

### Choose the Right Provider

- **Budget-friendly**: HuggingFace (free tier available)
- **Best quality**: OpenAI GPT-4 or Claude Opus
- **Balanced**: OpenAI GPT-3.5 or Claude Sonnet

### Batch Processing

Process multiple pages in batches to reduce overhead:

```python
async def process_pages_batch(page_ids: list[int]):
    tasks = [generate_meta_description(pid) for pid in page_ids]
    return await asyncio.gather(*tasks)
```

### Cache Results

Cache generated content to avoid regeneration:

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_description(page_id: int):
    return generate_meta_description(page_id)
```

## Multilingual Support

The system automatically detects page language and generates content accordingly:

```python
# French content
{
  "page_id": 5,
  "provider": "openai"
}
# Response will be in French if page.lang == "fr"
```

## Best Practices

### 1. Review Generated Content

Always review LLM-generated content before publishing:
- Verify factual accuracy
- Check keyword placement
- Ensure brand voice consistency

### 2. A/B Test Variations

Generate multiple variations and test performance:

```python
suggestions = generate_title_suggestions(page_id=1, count=5)
# Test each suggestion's CTR
```

### 3. Monitor API Costs

Track LLM API usage to control costs:
- Set budget limits
- Monitor token consumption
- Use cheaper models for drafts

### 4. Handle Rate Limits

Implement retry logic for rate limit errors:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_with_retry(page_id: int):
    return generate_meta_description(page_id)
```

## Error Handling

### Common Errors

**LLMAuthenticationException**: Invalid API key
```json
{
  "detail": "openai API key not configured"
}
```

**LLMRateLimitException**: Rate limit exceeded
```json
{
  "detail": "OpenAI rate limit exceeded"
}
```

**LLMContentFilterException**: Content filtered by safety systems
```json
{
  "detail": "Content filtered due to safety policy"
}
```

## Architecture

### Strategy Pattern

The system uses Strategy pattern for interchangeable LLM backends:

```
LLMFactory
  ├─ OpenAIAdapter (GPT-4, GPT-3.5)
  ├─ AnthropicAdapter (Claude 3)
  └─ HuggingFaceAdapter (Mistral, Llama)
```

### Service Layer

`ContentGenerationService` provides high-level methods:
- `generate_meta_description()`
- `generate_title_suggestions()`
- `generate_h1_suggestion()`
- `generate_content_recommendations()`

## Performance

### Token Usage

| Operation | Avg Tokens | Cost (GPT-3.5) |
|-----------|-----------|----------------|
| Meta description | 150-200 | $0.0003 |
| Title suggestions | 200-300 | $0.0005 |
| Recommendations | 500-800 | $0.0012 |

### Speed

| Provider | Avg Response Time |
|----------|------------------|
| OpenAI | 1-3 seconds |
| Anthropic | 1-2 seconds |
| HuggingFace | 3-10 seconds |

## Roadmap

Future enhancements:
- [ ] Bulk content generation endpoints
- [ ] Custom prompt templates
- [ ] Content scheduling
- [ ] Quality scoring
- [ ] Plagiarism detection
- [ ] Brand voice training

## API Reference

See [API Documentation](http://localhost:8000/docs) for complete endpoint reference.

### Endpoints

- `POST /api/v1/content/meta-description` - Generate meta description
- `POST /api/v1/content/title-suggestions` - Generate title suggestions  
- `POST /api/v1/content/recommendations` - Generate content recommendations
- `GET /api/v1/content/providers` - List available providers and models
