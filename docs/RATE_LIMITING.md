# Rate Limiting & Quotas

## Overview

SEO SaaS Tool implements comprehensive rate limiting and quota management to ensure fair resource usage across all tenants. The system uses a combination of Redis for fast in-memory counters and PostgreSQL for persistent tracking and analytics.

## Rate Limit Strategy

### Multi-Tier Approach

1. **Request-Level Limiting**: All API requests count toward monthly quotas
2. **Resource-Level Limiting**: Specific operations (crawls, analysis) have separate limits
3. **Plan-Based Quotas**: Limits vary based on subscription plan
4. **Real-time Tracking**: Redis provides instant feedback on current usage

## Subscription Plans & Quotas

### Free Plan

| Resource | Limit |
|----------|-------|
| API Calls/Month | 10,000 |
| Projects | 1 |
| Pages/Crawl | 100 |
| Analysis Requests/Month | 100 |
| Crawl Jobs/Month | 10 |

### Starter Plan

| Resource | Limit |
|----------|-------|
| API Calls/Month | 50,000 |
| Projects | 5 |
| Pages/Crawl | 1,000 |
| Analysis Requests/Month | 1,000 |
| Crawl Jobs/Month | 50 |

### Pro Plan

| Resource | Limit |
|----------|-------|
| API Calls/Month | 200,000 |
| Projects | 50 |
| Pages/Crawl | 10,000 |
| Analysis Requests/Month | 10,000 |
| Crawl Jobs/Month | 500 |

### Enterprise Plan

| Resource | Limit |
|----------|-------|
| API Calls/Month | 1,000,000 |
| Projects | 500 |
| Pages/Crawl | 100,000 |
| Analysis Requests/Month | 100,000 |
| Crawl Jobs/Month | 5,000 |

## HTTP Headers

All API responses include rate limit information in HTTP headers:

```http
X-RateLimit-Limit: 10000
X-RateLimit-Remaining: 9523
X-RateLimit-Reset: 1709251200
```

### Header Descriptions

- **`X-RateLimit-Limit`**: Maximum requests allowed in the current period
- **`X-RateLimit-Remaining`**: Number of requests remaining
- **`X-RateLimit-Reset`**: Unix timestamp when the quota resets (first day of next month)

## Error Responses

When rate limit is exceeded, the API returns a `429 Too Many Requests` response:

```json
{
  "detail": "Monthly API quota exceeded. Limit: 10000",
  "limit_type": "monthly",
  "limit": 10000,
  "current": 10001,
  "reset_at": "2024-03-01T00:00:00"
}
```

### HTTP Status Codes

- **`429 Too Many Requests`**: Rate limit exceeded
- **`403 Forbidden`**: Plan upgrade required for feature
- **`200 OK`**: Request successful with rate limit headers

## API Usage

### Check Current Quota

```bash
curl -X GET http://localhost:8000/api/v1/usage/quota \
  -H "X-API-Key: YOUR_API_KEY"
```

Response:
```json
{
  "plan": "pro",
  "max_projects": 50,
  "max_pages_per_crawl": 10000,
  "max_api_calls_per_month": 200000,
  "current_usage": {
    "period": "2024-02",
    "total_api_calls": 5234,
    "crawl_jobs": 12,
    "pages_crawled": 8450,
    "analysis_requests": 45
  },
  "remaining": {
    "api_calls": 194766,
    "projects": 50,
    "pages_per_crawl": 10000
  }
}
```

### Get Usage Statistics

```bash
# Current month
curl -X GET http://localhost:8000/api/v1/usage/stats \
  -H "X-API-Key: YOUR_API_KEY"

# Specific month
curl -X GET "http://localhost:8000/api/v1/usage/stats?year=2024&month=1" \
  -H "X-API-Key: YOUR_API_KEY"
```

Response:
```json
{
  "period": "2024-02",
  "total_api_calls": 5234,
  "crawl_jobs": 12,
  "pages_crawled": 8450,
  "analysis_requests": 45
}
```

### Get Usage History

```bash
# Last 6 months (default)
curl -X GET http://localhost:8000/api/v1/usage/history \
  -H "X-API-Key: YOUR_API_KEY"

# Last 12 months
curl -X GET "http://localhost:8000/api/v1/usage/history?months=12" \
  -H "X-API-Key: YOUR_API_KEY"
```

Response:
```json
{
  "history": [
    {
      "period": "2024-02",
      "total_api_calls": 5234,
      "crawl_jobs": 12,
      "pages_crawled": 8450,
      "analysis_requests": 45
    },
    {
      "period": "2024-01",
      "total_api_calls": 8901,
      "crawl_jobs": 23,
      "pages_crawled": 15230,
      "analysis_requests": 89
    }
  ]
}
```

### Get Rate Limits

```bash
curl -X GET http://localhost:8000/api/v1/usage/limits \
  -H "X-API-Key: YOUR_API_KEY"
```

Response:
```json
{
  "plan": "pro",
  "limits": {
    "api_calls_per_month": 200000,
    "max_projects": 50,
    "max_pages_per_crawl": 10000,
    "analysis_requests_per_month": 10000,
    "crawl_jobs_per_month": 500
  },
  "reset_at": "2024-03-01T00:00:00",
  "reset_timestamp": 1709251200
}
```

## Client Integration

### Python Client Example

```python
import requests
import time

class SEOClient:
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}

    def _check_rate_limit(self, response):
        """Check rate limit headers from response."""
        if response.status_code == 429:
            reset_at = int(response.headers.get("X-RateLimit-Reset", 0))
            wait_time = max(0, reset_at - int(time.time()))
            raise Exception(f"Rate limit exceeded. Reset in {wait_time} seconds")

        # Log current rate limit status
        limit = response.headers.get("X-RateLimit-Limit")
        remaining = response.headers.get("X-RateLimit-Remaining")
        print(f"Rate limit: {remaining}/{limit} remaining")

    def get_quota(self):
        """Get current quota and usage."""
        response = requests.get(
            f"{self.base_url}/usage/quota",
            headers=self.headers
        )
        self._check_rate_limit(response)
        return response.json()

    def start_crawl(self, project_id: int, **kwargs):
        """Start a crawl with automatic quota checking."""
        # Check quota first
        quota = self.get_quota()
        if quota["remaining"]["api_calls"] < 100:
            raise Exception("Low API quota. Consider upgrading plan.")

        response = requests.post(
            f"{self.base_url}/crawl/",
            headers=self.headers,
            json={"project_id": project_id, **kwargs}
        )
        self._check_rate_limit(response)
        return response.json()

# Usage
client = SEOClient(api_key="sk_test_...")
quota = client.get_quota()
print(f"Plan: {quota['plan']}")
print(f"API calls remaining: {quota['remaining']['api_calls']}")
```

### JavaScript/TypeScript Client Example

```typescript
class SEOClient {
  private apiKey: string;
  private baseUrl: string;

  constructor(apiKey: string, baseUrl: string = "http://localhost:8000/api/v1") {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
  }

  private checkRateLimit(response: Response): void {
    if (response.status === 429) {
      const resetAt = parseInt(response.headers.get("X-RateLimit-Reset") || "0");
      const waitTime = Math.max(0, resetAt - Math.floor(Date.now() / 1000));
      throw new Error(`Rate limit exceeded. Reset in ${waitTime} seconds`);
    }

    const limit = response.headers.get("X-RateLimit-Limit");
    const remaining = response.headers.get("X-RateLimit-Remaining");
    console.log(`Rate limit: ${remaining}/${limit} remaining`);
  }

  async getQuota(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/usage/quota`, {
      headers: { "X-API-Key": this.apiKey }
    });
    this.checkRateLimit(response);
    return response.json();
  }

  async startCrawl(projectId: number, options: any): Promise<any> {
    // Check quota first
    const quota = await this.getQuota();
    if (quota.remaining.api_calls < 100) {
      throw new Error("Low API quota. Consider upgrading plan.");
    }

    const response = await fetch(`${this.baseUrl}/crawl/`, {
      method: "POST",
      headers: {
        "X-API-Key": this.apiKey,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ project_id: projectId, ...options })
    });
    this.checkRateLimit(response);
    return response.json();
  }
}

// Usage
const client = new SEOClient("sk_test_...");
const quota = await client.getQuota();
console.log(`Plan: ${quota.plan}`);
console.log(`API calls remaining: ${quota.remaining.api_calls}`);
```

## Best Practices

### 1. Check Quota Before Expensive Operations

Always check remaining quota before starting crawls or analysis:

```bash
# Check quota
QUOTA=$(curl -s http://localhost:8000/api/v1/usage/quota \
  -H "X-API-Key: $API_KEY" | jq '.remaining.api_calls')

if [ $QUOTA -lt 100 ]; then
  echo "Low quota: $QUOTA remaining"
  exit 1
fi

# Proceed with crawl
curl -X POST http://localhost:8000/api/v1/crawl/ \
  -H "X-API-Key: $API_KEY" \
  -d '{"project_id": 1, "mode": "fast"}'
```

### 2. Handle 429 Responses Gracefully

Implement exponential backoff when rate limited:

```python
import time
from typing import Callable

def with_retry(func: Callable, max_retries: int = 3):
    """Retry function with exponential backoff on rate limit."""
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = min(2 ** attempt, 60)  # Max 60 seconds
            print(f"Rate limited. Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
```

### 3. Monitor Usage Trends

Track usage over time to predict when upgrades are needed:

```python
def analyze_usage_trend(client: SEOClient):
    """Analyze usage trends and predict quota exhaustion."""
    history = client.get_usage_history(months=3)

    # Calculate average monthly growth
    if len(history) >= 2:
        growth_rate = (
            history[0]["total_api_calls"] - history[1]["total_api_calls"]
        ) / history[1]["total_api_calls"]

        print(f"Monthly growth rate: {growth_rate * 100:.1f}%")

        if growth_rate > 0.5:  # >50% growth
            print("⚠️ High growth detected. Consider upgrading plan.")
```

### 4. Cache Responses

Reduce API calls by caching responses locally:

```python
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def get_cached_page(page_id: int):
    """Cache page data for 5 minutes."""
    # Implementation with TTL
    pass
```

## Quota Reset Schedule

Quotas reset on the **first day of each month at 00:00:00 UTC**.

### Next Reset Times

Calculate next reset programmatically:

```python
from datetime import datetime

def get_next_reset():
    """Get next quota reset time."""
    now = datetime.utcnow()
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1)
    else:
        next_month = datetime(now.year, now.month + 1, 1)
    return next_month

reset_at = get_next_reset()
print(f"Quota resets at: {reset_at.isoformat()}")
```

## Plan Upgrades

Contact support or use the billing portal to upgrade your plan when:

- Consistently hitting 80%+ of quota
- Receiving 429 errors regularly
- Need higher limits for specific resources

## Monitoring & Alerts

### Set Up Alerts

Monitor quota usage and set up alerts:

```python
def check_quota_threshold(client: SEOClient, threshold: float = 0.8):
    """Alert when quota usage exceeds threshold."""
    quota = client.get_quota()
    usage_percent = quota["current_usage"]["total_api_calls"] / quota["max_api_calls_per_month"]

    if usage_percent >= threshold:
        print(f"⚠️ ALERT: {usage_percent * 100:.1f}% of monthly quota used")
        # Send notification (email, Slack, etc.)
        return True
    return False
```

### Prometheus Metrics

If Prometheus is enabled, rate limit metrics are exported:

```
# HELP api_requests_total Total API requests
# TYPE api_requests_total counter
api_requests_total{tenant="default",status="200"} 5234

# HELP quota_usage_percent Current quota usage percentage
# TYPE quota_usage_percent gauge
quota_usage_percent{tenant="default"} 0.52
```

## Troubleshooting

### "429 Too Many Requests" Error

**Problem**: Receiving 429 errors frequently

**Solutions**:
1. Check current quota: `GET /usage/quota`
2. Review usage history: `GET /usage/history`
3. Implement caching to reduce redundant calls
4. Upgrade to higher plan if consistently hitting limits
5. Optimize crawl configurations (reduce depth, pages)

### Quota Not Updating

**Problem**: Usage statistics not incrementing

**Solutions**:
1. Check Redis connection: `redis-cli ping`
2. Verify middleware is enabled in `app/main.py`
3. Check logs for errors: `docker-compose logs backend`
4. Restart backend service: `docker-compose restart backend`

### Incorrect Reset Time

**Problem**: Quota shows wrong reset time

**Solutions**:
1. Verify server timezone is UTC
2. Check system clock: `date -u`
3. Restart services to sync time

## Database Schema

### APIUsage Table

```sql
CREATE TABLE api_usage (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,  -- 1-12
    total_api_calls INTEGER DEFAULT 0,
    crawl_jobs INTEGER DEFAULT 0,
    pages_crawled INTEGER DEFAULT 0,
    analysis_requests INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_usage_tenant_period ON api_usage(tenant_id, year, month);
```

### RateLimitLog Table

```sql
CREATE TABLE rate_limit_logs (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    endpoint VARCHAR(500) NOT NULL,
    method VARCHAR(10) NOT NULL,
    ip_address VARCHAR(45),
    limit_type VARCHAR(50) NOT NULL,
    limit_value INTEGER NOT NULL,
    current_usage INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_rate_limit_logs_tenant ON rate_limit_logs(tenant_id, created_at);
```

## API Reference

Full API documentation available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Relevant endpoints:
- `GET /api/v1/usage/quota` - Current quota and usage
- `GET /api/v1/usage/stats` - Usage statistics for period
- `GET /api/v1/usage/history` - Historical usage data
- `GET /api/v1/usage/limits` - Rate limit configuration

## Next Steps

- Read the [Quick Start Guide](./QUICKSTART.md)
- Learn about [Crawler Modes](./CRAWLER.md)
- Check the [Architecture Documentation](./ARCHITECTURE.md)
