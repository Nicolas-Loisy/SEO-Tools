# Crawler Documentation

## Overview

SEO SaaS Tool provides two crawler modes for maximum flexibility:

1. **Fast Mode** (`mode: "fast"`): Lightning-fast crawler using aiohttp for static HTML sites
2. **JS Mode** (`mode: "js"`): Playwright-powered crawler with full JavaScript execution support

## Crawler Modes

### Fast Crawler (Default)

**Technology**: aiohttp + BeautifulSoup
**Best for**: Static HTML sites, blogs, traditional websites
**Speed**: Very fast (~100-500ms per page)
**JavaScript**: ❌ Not supported

**Features**:
- Asynchronous HTTP requests with connection pooling
- HTML parsing with BeautifulSoup
- Automatic retry with exponential backoff
- Concurrent crawling (up to 10 pages simultaneously)
- Very low resource usage

**Use cases**:
- WordPress blogs
- Static marketing sites
- Documentation sites
- Traditional CMS-based websites

### Playwright Crawler (JS Mode)

**Technology**: Playwright (Chromium)
**Best for**: Modern SPAs, React/Vue/Angular apps, JavaScript-heavy sites
**Speed**: Slower (~2-5 seconds per page)
**JavaScript**: ✅ Full support

**Features**:
- Full JavaScript execution in real browser
- Waits for dynamic content to load
- Screenshot capture (viewport or full page)
- JavaScript error detection and logging
- Resource blocking for performance optimization
- Custom viewport sizes (mobile/desktop/tablet)
- Configurable wait conditions

**Use cases**:
- Single Page Applications (SPAs)
- React, Vue, Angular applications
- Sites with client-side rendering
- Dynamic content loaded via AJAX
- Sites requiring screenshot analysis

## API Usage

### Basic Crawl (Fast Mode)

```bash
curl -X POST http://localhost:8000/api/v1/crawl/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "project_id": 1,
    "mode": "fast",
    "config": {
      "depth": 2,
      "max_pages": 50
    }
  }'
```

### JavaScript Crawl with Screenshots

```bash
curl -X POST http://localhost:8000/api/v1/crawl/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "project_id": 1,
    "mode": "js",
    "config": {
      "depth": 3,
      "max_pages": 100,
      "headless": true,
      "capture_screenshot": true,
      "screenshot_type": "viewport",
      "viewport": {
        "width": 1920,
        "height": 1080
      },
      "wait_until": "networkidle",
      "timeout": 30000,
      "block_resources": ["image", "font", "media"]
    }
  }'
```

### Mobile Crawl

```bash
curl -X POST http://localhost:8000/api/v1/crawl/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "project_id": 1,
    "mode": "js",
    "config": {
      "depth": 2,
      "max_pages": 50,
      "viewport": {
        "width": 375,
        "height": 667
      },
      "wait_until": "networkidle"
    }
  }'
```

## Configuration Options

### Common Options (Both Modes)

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `depth` | int | Project setting | Maximum crawl depth (0-10) |
| `max_pages` | int | Project setting | Maximum pages to crawl (1-100,000) |

### Playwright-Specific Options (JS Mode Only)

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `headless` | bool | `true` | Run browser in headless mode |
| `capture_screenshot` | bool | `false` | Capture page screenshots |
| `screenshot_type` | string | `"viewport"` | Screenshot type: `"viewport"` or `"fullpage"` |
| `viewport` | object | `{width: 1920, height: 1080}` | Browser viewport size |
| `wait_until` | string | `"networkidle"` | Wait condition: `"load"`, `"domcontentloaded"`, or `"networkidle"` |
| `timeout` | int | `30000` | Page load timeout in milliseconds (5000-120000) |
| `block_resources` | array | `["image", "font", "media"]` | Resource types to block for performance |

### Wait Until Conditions

- **`load`**: Wait for `window.onload` event (fastest)
- **`domcontentloaded`**: Wait for DOM to be fully loaded (fast)
- **`networkidle`**: Wait for network to be idle (most reliable, recommended)

### Resource Blocking

Block unnecessary resources to speed up crawling:

- `image`: Block images
- `font`: Block web fonts
- `media`: Block audio/video
- `stylesheet`: Block CSS (not recommended)
- `script`: Block scripts (breaks JS execution!)

**Recommended for performance**: `["image", "font", "media"]`

## Python Client Example

```python
import requests

API_KEY = "sk_test_..."
BASE_URL = "http://localhost:8000/api/v1"

def crawl_spa_with_screenshots(project_id: int):
    """Crawl a Single Page Application with screenshots."""

    # Start crawl
    response = requests.post(
        f"{BASE_URL}/crawl/",
        headers={"X-API-Key": API_KEY},
        json={
            "project_id": project_id,
            "mode": "js",
            "config": {
                "depth": 3,
                "max_pages": 100,
                "headless": True,
                "capture_screenshot": True,
                "screenshot_type": "fullpage",
                "viewport": {"width": 1920, "height": 1080},
                "wait_until": "networkidle",
                "timeout": 45000,
                "block_resources": ["font", "media"],
            },
        },
    )

    job = response.json()
    job_id = job["id"]
    print(f"Crawl job started: {job_id}")

    # Poll for completion
    import time
    while True:
        status_response = requests.get(
            f"{BASE_URL}/crawl/{job_id}",
            headers={"X-API-Key": API_KEY},
        )
        job_status = status_response.json()

        if job_status["status"] in ["completed", "failed"]:
            break

        print(f"Status: {job_status['status']}, Pages: {job_status['pages_crawled']}")
        time.sleep(5)

    print(f"Crawl completed!")
    print(f"Pages discovered: {job_status['pages_discovered']}")
    print(f"Pages crawled: {job_status['pages_crawled']}")
    print(f"Links found: {job_status['links_found']}")

    return job_status

# Usage
crawl_spa_with_screenshots(project_id=1)
```

## Performance Comparison

| Metric | Fast Mode | JS Mode (No Screenshots) | JS Mode (With Screenshots) |
|--------|-----------|-------------------------|---------------------------|
| **Speed per page** | 100-500ms | 2-3 seconds | 3-5 seconds |
| **Memory usage** | ~50-100MB | ~500MB-1GB | ~800MB-1.5GB |
| **CPU usage** | Very low | Medium | High |
| **Concurrent pages** | Up to 10 | Sequential | Sequential |
| **Best for** | Static sites | SPAs, dynamic sites | Visual analysis |

## Best Practices

### 1. Choose the Right Mode

- **Use Fast Mode when**:
  - Site is mostly static HTML
  - Speed is critical
  - You don't need JavaScript execution
  - Crawling large sites (10,000+ pages)

- **Use JS Mode when**:
  - Site heavily relies on JavaScript
  - Content is loaded dynamically
  - You need screenshots
  - Crawling modern SPAs

### 2. Optimize Playwright Performance

```json
{
  "headless": true,              // Always use headless in production
  "block_resources": ["image", "font", "media"],  // Block unnecessary resources
  "wait_until": "domcontentloaded",  // Use faster wait condition if networkidle is slow
  "timeout": 20000,              // Reduce timeout for faster failures
  "capture_screenshot": false    // Disable if not needed
}
```

### 3. Respect Rate Limits

Set appropriate delays in your project settings:
- Fast mode: 0.5-1 second delay
- JS mode: 1-2 second delay

### 4. Monitor Resource Usage

Use Flower to monitor Celery workers:
```bash
open http://localhost:5555
```

### 5. Handle Large Sites

For sites with 1000+ pages:
- Use Fast mode when possible
- Increase max_pages gradually
- Set reasonable depth limits (2-3)
- Use scheduled crawls instead of manual

## Troubleshooting

### JS Mode Issues

**Problem**: "Timeout exceeded"
```json
{
  "timeout": 60000,           // Increase timeout
  "wait_until": "domcontentloaded"  // Use faster condition
}
```

**Problem**: "Out of memory"
```json
{
  "block_resources": ["image", "font", "media", "stylesheet"],  // Block more resources
  "max_pages": 50            // Reduce page count
}
```

**Problem**: "Screenshot too large"
```json
{
  "screenshot_type": "viewport"  // Use viewport instead of fullpage
}
```

### Fast Mode Issues

**Problem**: "Missing content"
- Switch to JS mode - site likely uses JavaScript

**Problem**: "Connection timeout"
- Check project's `crawl_delay` setting
- Verify site is accessible

## JavaScript Error Detection

When using JS mode, JavaScript errors are automatically captured:

```python
# Get crawl results
job = get_crawl_job(job_id)

# Check for JS errors in failed pages
for error in job.errors:
    if error.get("js_errors"):
        print(f"Page {error['url']} has JS errors:")
        for js_error in error["js_errors"]:
            print(f"  - {js_error}")
```

## Screenshot Storage

Currently, screenshots are stored in the `rendered_html` field (truncated).

**TODO**: Future implementation will store screenshots in MinIO/S3 with references in the database.

## Examples by Use Case

### E-commerce Site (Product Pages)

```json
{
  "mode": "js",
  "config": {
    "depth": 3,
    "max_pages": 500,
    "wait_until": "networkidle",
    "capture_screenshot": true,
    "viewport": {"width": 1920, "height": 1080}
  }
}
```

### Blog/News Site

```json
{
  "mode": "fast",
  "config": {
    "depth": 2,
    "max_pages": 1000
  }
}
```

### React SPA

```json
{
  "mode": "js",
  "config": {
    "depth": 4,
    "max_pages": 200,
    "wait_until": "networkidle",
    "timeout": 45000,
    "block_resources": ["font", "media"]
  }
}
```

### Mobile App Landing Page

```json
{
  "mode": "js",
  "config": {
    "depth": 1,
    "max_pages": 10,
    "viewport": {"width": 375, "height": 667},
    "capture_screenshot": true,
    "screenshot_type": "fullpage"
  }
}
```

## API Reference

See the [API Documentation](http://localhost:8000/docs) for complete endpoint reference.

### Relevant Endpoints

- `POST /api/v1/crawl/` - Start a new crawl
- `GET /api/v1/crawl/{job_id}` - Get crawl job status
- `GET /api/v1/crawl/project/{project_id}` - List all crawls for a project
- `GET /api/v1/pages/?project_id={id}` - Get crawled pages

## Next Steps

- Read the [Quick Start Guide](./QUICKSTART.md)
- Learn about [Multilingual Support](./MULTILINGUAL.md)
- Check the [Architecture Documentation](./ARCHITECTURE.md)
