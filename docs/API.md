# API Documentation

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently, the API is open for development. Production will require API key authentication.

```http
Authorization: Bearer YOUR_API_KEY
```

## Endpoints

### Projects

#### Create Project

```http
POST /projects/
Content-Type: application/json

{
  "name": "My Website",
  "domain": "https://example.com",
  "description": "Main company website",
  "js_enabled": false,
  "max_depth": 3,
  "max_pages": 1000,
  "crawl_delay": 1.0,
  "respect_robots": true
}
```

**Response:** `201 Created`

```json
{
  "id": 1,
  "tenant_id": 1,
  "name": "My Website",
  "domain": "https://example.com",
  "js_enabled": false,
  "max_depth": 3,
  "max_pages": 1000,
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "last_crawl_at": null
}
```

#### List Projects

```http
GET /projects/?skip=0&limit=100
```

**Response:** `200 OK`

```json
[
  {
    "id": 1,
    "name": "My Website",
    "domain": "https://example.com",
    ...
  }
]
```

#### Get Project

```http
GET /projects/{project_id}
```

**Response:** `200 OK` or `404 Not Found`

#### Update Project

```http
PUT /projects/{project_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "max_pages": 2000
}
```

**Response:** `200 OK`

#### Delete Project

```http
DELETE /projects/{project_id}
```

**Response:** `204 No Content`

---

### Crawl Jobs

#### Start Crawl

```http
POST /crawl/
Content-Type: application/json

{
  "project_id": 1,
  "mode": "fast",
  "config": {
    "depth": 3,
    "max_pages": 500,
    "wait_for_selector": null
  }
}
```

**Modes:**
- `fast`: Static HTML crawling (Scrapy)
- `js`: JavaScript rendering (Playwright)

**Response:** `201 Created`

```json
{
  "id": 1,
  "project_id": 1,
  "status": "pending",
  "mode": "fast",
  "config": {
    "depth": 3,
    "max_pages": 500
  },
  "started_at": null,
  "finished_at": null,
  "duration_seconds": 0.0,
  "pages_discovered": 0,
  "pages_crawled": 0,
  "pages_failed": 0,
  "links_found": 0,
  "error_message": null,
  "celery_task_id": "abc123...",
  "created_at": "2024-01-15T10:35:00Z"
}
```

#### Get Crawl Job Status

```http
GET /crawl/{job_id}
```

**Response:** `200 OK`

```json
{
  "id": 1,
  "status": "completed",
  "pages_discovered": 150,
  "pages_crawled": 150,
  "pages_failed": 5,
  "duration_seconds": 120.5,
  ...
}
```

**Status Values:**
- `pending`: Queued, not started
- `running`: Currently executing
- `completed`: Successfully finished
- `failed`: Encountered error
- `cancelled`: Manually stopped

#### List Project Crawl Jobs

```http
GET /crawl/project/{project_id}?skip=0&limit=50
```

**Response:** `200 OK`

```json
[
  {
    "id": 1,
    "status": "completed",
    ...
  },
  {
    "id": 2,
    "status": "running",
    ...
  }
]
```

---

### Pages

#### List Pages

```http
GET /pages/?project_id=1&status_code=200&skip=0&limit=50
```

**Query Parameters:**
- `project_id` (optional): Filter by project
- `status_code` (optional): Filter by HTTP status
- `min_depth` (optional): Minimum crawl depth
- `max_depth` (optional): Maximum crawl depth
- `skip`: Pagination offset (default: 0)
- `limit`: Results per page (default: 50, max: 500)

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": 1,
      "project_id": 1,
      "url": "https://example.com/",
      "canonical_url": "https://example.com/",
      "status_code": 200,
      "content_type": "text/html",
      "title": "Home - Example",
      "meta_description": "Welcome to Example.com",
      "h1": "Welcome",
      "word_count": 500,
      "depth": 0,
      "seo_score": 85.5,
      "discovered_at": "2024-01-15T10:35:00Z",
      "last_crawled_at": "2024-01-15T10:40:00Z"
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 50
}
```

#### Get Page Details

```http
GET /pages/{page_id}
```

**Response:** `200 OK`

```json
{
  "id": 1,
  "url": "https://example.com/",
  "title": "Home - Example",
  "meta_description": "...",
  "word_count": 500,
  ...
}
```

---

## Error Responses

### 400 Bad Request

```json
{
  "detail": [
    {
      "loc": ["body", "domain"],
      "msg": "invalid or missing URL scheme",
      "type": "value_error.url.scheme"
    }
  ]
}
```

### 404 Not Found

```json
{
  "detail": "Project 999 not found"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

(Coming soon)

- Free tier: 100 requests/hour
- Pro tier: 1000 requests/hour
- Enterprise: Custom limits

---

## Webhooks

(Coming soon)

Configure webhooks to receive notifications:

```json
{
  "event": "crawl.completed",
  "data": {
    "job_id": 1,
    "project_id": 1,
    "pages_crawled": 150
  }
}
```

**Events:**
- `crawl.started`
- `crawl.completed`
- `crawl.failed`
- `content.generated`
- `schema.generated`

---

## OpenAPI Specification

Interactive API documentation available at:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json
