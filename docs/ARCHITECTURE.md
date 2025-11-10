# Architecture Documentation

## System Overview

The SEO SaaS Tool is a multi-tenant platform designed for scalability, maintainability, and extensibility. It follows a microservices-inspired architecture with clear separation of concerns.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│                    (React + Tailwind)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                             │
│                    (Nginx/Traefik)                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Auth   │  │Projects  │  │  Crawl   │  │  Pages   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└──────┬────────────────┬────────────────┬───────────────────┘
       │                │                │
       ▼                ▼                ▼
┌──────────┐      ┌──────────┐    ┌──────────┐
│PostgreSQL│      │  Redis   │    │Meilisearch│
│+pgvector │      │(Cache/Q) │    │ (Search) │
└──────────┘      └────┬─────┘    └──────────┘
                       │
                       ▼
              ┌────────────────┐
              │ Celery Workers │
              │  - Crawler     │
              │  - Content     │
              │  - Analysis    │
              └───────┬────────┘
                      │
                      ▼
              ┌────────────────┐
              │  MinIO (S3)    │
              │   Storage      │
              └────────────────┘
```

## Component Details

### Backend API (FastAPI)

**Responsibilities:**
- REST API endpoints
- Request validation (Pydantic)
- Authentication & authorization
- Business logic orchestration
- Job queueing

**Key Modules:**
- `api/v1/endpoints/`: Route handlers
- `api/v1/schemas/`: Request/response schemas
- `core/`: Configuration, database, Redis
- `models/`: SQLAlchemy ORM models
- `repositories/`: Data access layer (Repository pattern)
- `services/`: Business logic services

### Database Layer (PostgreSQL + pgvector)

**Schema:**
- `tenants`: Multi-tenant isolation
- `projects`: Website projects
- `pages`: Crawled pages with embeddings
- `links`: Internal link graph
- `crawl_jobs`: Crawl execution tracking
- `site_trees`: Generated site architectures
- `content_drafts`: AI-generated content
- `schema_suggestions`: Structured data

**Extensions:**
- `pgvector`: Vector similarity search for semantic analysis

### Workers (Celery)

**Queues:**
- `crawler`: Web crawling tasks
- `content`: Content generation
- `analysis`: SEO analysis, embeddings, graph computation

**Tasks:**
- `crawl_site`: Execute website crawl
- `generate_site_tree`: Create site architecture
- `generate_content`: AI content generation
- `compute_internal_linking_graph`: Build link graph
- `compute_page_embeddings`: Generate semantic vectors
- `generate_schema_suggestions`: Create structured data

### Crawler Service

**Factory Pattern:**
```python
CrawlerFactory
  ├── ScrapyCrawler (fast mode)
  └── PlaywrightCrawler (JS-enabled mode)
```

**Features:**
- Robots.txt compliance
- Rate limiting
- Depth control
- Link extraction
- Content hashing
- Screenshot capture (JS mode)

### LLM Integration (Adapter Pattern)

**Adapters:**
```python
LLMAdapter (interface)
  ├── OpenAIAdapter
  ├── AnthropicAdapter
  └── HuggingFaceAdapter
```

**Use Cases:**
- Site tree generation
- Content creation
- Schema.org generation
- Keyword analysis

## Design Patterns

### 1. Factory Pattern
**Location:** `services/crawler/factory.py`

```python
class CrawlerFactory:
    @staticmethod
    def create(mode: str, config: dict) -> BaseCrawler:
        if mode == "fast":
            return ScrapyCrawler(config)
        elif mode == "js":
            return PlaywrightCrawler(config)
```

**Purpose:** Select crawler implementation based on JS requirement

### 2. Repository Pattern
**Location:** `repositories/`

```python
class PageRepository:
    async def create(page: Page) -> Page
    async def get_by_id(id: int) -> Page
    async def find_by_url(url: str) -> Page
    async def list_by_project(project_id: int) -> List[Page]
```

**Purpose:** Decouple data access from business logic

### 3. Strategy Pattern
**Location:** `services/analysis/strategies/`

```python
class ScoringStrategy(ABC):
    def score(page: Page) -> float

class PageRankStrategy(ScoringStrategy): ...
class TFIDFStrategy(ScoringStrategy): ...
class EmbeddingStrategy(ScoringStrategy): ...
```

**Purpose:** Interchangeable SEO scoring algorithms

### 4. Command Pattern
**Location:** `models/crawl.py`

```python
class CrawlJob:
    config: dict  # Encapsulates all crawl parameters
    status: str

    def execute()
    def replay()
```

**Purpose:** Encapsulate crawl requests for history/replay

### 5. Adapter Pattern
**Location:** `adapters/llm/`

```python
class LLMAdapter(ABC):
    def generate_text(prompt: str) -> str
    def generate_structured(schema: dict) -> dict
```

**Purpose:** Unified interface for different LLM providers

### 6. Observer Pattern
**Location:** `core/events.py`

```python
class EventBus:
    def publish(event: str, data: dict)
    def subscribe(event: str, handler: Callable)

# Example:
event_bus.publish("crawl.completed", {"job_id": 1})
```

**Purpose:** Decouple event notification (webhooks, UI updates)

## Data Flow

### Crawl Execution Flow

```
1. User creates crawl job via API
   POST /api/v1/crawl/

2. API validates & stores CrawlJob
   Status: "pending"

3. API enqueues Celery task
   crawl_site.delay(job_id)

4. Worker picks up task
   - Updates status: "running"
   - Factory creates crawler
   - Crawler executes

5. Crawler discovers pages
   - Extracts metadata
   - Saves to database
   - Computes embeddings (async)
   - Builds link graph

6. Worker completes
   - Updates status: "completed"
   - Publishes event
   - Sends webhook notification
```

### Content Generation Flow

```
1. User requests site tree
   POST /api/v1/projects/{id}/site-tree/generate

2. API validates & enqueues task
   generate_site_tree.delay(project_id, keyword, depth)

3. Worker executes
   - LLM Adapter selects provider
   - Generates tree structure
   - Saves to SiteTree model

4. Returns tree JSON
   {
     "category": "Home",
     "children": [...]
   }
```

## Security Architecture

### Multi-Tenancy

- **Row-Level Security:** All queries filtered by `tenant_id`
- **API Keys:** Scoped to tenant
- **Data Isolation:** Foreign keys cascade to tenant

### Authentication

- **API Keys:** Bearer token authentication
- **OAuth2:** Future implementation
- **RBAC:** Role-based access control

### Data Protection

- **TLS:** All connections encrypted
- **Secrets:** Environment variables, Vault integration
- **Database:** Encrypted at rest (cloud provider)

## Scaling Considerations

### Horizontal Scaling

- **API:** Stateless, scale behind load balancer
- **Workers:** Add more Celery workers per queue
- **Database:** Read replicas, connection pooling
- **Redis:** Redis Cluster for high availability

### Vertical Scaling

- **Database:** Increase resources for complex queries
- **Workers:** More CPU/RAM for crawling tasks

### Caching Strategy

- **Redis:** API responses, page metadata
- **Meilisearch:** Full-text search cache
- **CDN:** Static assets (frontend)

## Monitoring & Observability

### Metrics (Prometheus)

- Request rate, latency, errors
- Worker queue length
- Database connections
- Crawl job statistics

### Logging

- Structured JSON logs
- Centralized via ELK stack
- Log levels: DEBUG, INFO, WARNING, ERROR

### Tracing (Jaeger)

- Distributed tracing across services
- Request flow visualization
- Performance bottleneck identification

## Deployment

### Development

```bash
docker-compose up
```

### Production

- **Kubernetes:** Helm charts
- **Cloud:** AWS ECS, GKE, Azure Container Apps
- **Database:** Managed PostgreSQL (RDS, Cloud SQL)
- **Redis:** Managed Redis (ElastiCache, MemoryStore)

## Future Enhancements

1. **GraphQL API:** Alternative to REST
2. **gRPC:** Inter-service communication
3. **Event Sourcing:** Audit trail, replay
4. **CQRS:** Separate read/write models
5. **Service Mesh:** Istio for microservices
