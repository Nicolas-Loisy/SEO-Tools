# SEO SaaS Tool

> Complete SEO analysis and optimization platform - From crawling to content generation

A comprehensive, multi-tenant SaaS platform for SEO professionals, providing web crawling (with JavaScript rendering), internal linking analysis, site architecture generation, content creation, and structured data management.

## Features

### Core Capabilities

- **Web Crawling**
  - Fast mode (Scrapy/Requests) for static sites
  - JavaScript-enabled mode (Playwright) for dynamic sites
  - Configurable depth, delays, and selectors
  - Robots.txt compliance

- **Internal Linking Analysis**
  - Graph-based link structure visualization
  - PageRank-like scoring
  - Automatic linking recommendations using semantic similarity
  - Interactive graph exploration

- **Site Architecture Generator**
  - AI-powered site tree generation
  - Keyword-based structure planning
  - Automatic slug and meta generation
  - Export to JSON, CSV, XML

- **Content Generation**
  - SEO-optimized article creation
  - Heading structure (H1-H3) generation
  - LSI keyword suggestions
  - Readability scoring

- **Structured Data**
  - Automatic schema.org detection
  - JSON-LD generation
  - OpenGraph and Twitter Card tags
  - Rich snippet validation

- **Multi-Tenant SaaS**
  - Complete data isolation
  - Flexible pricing plans
  - API key authentication
  - Usage quotas and billing

## Architecture

### Tech Stack

- **Backend**: FastAPI (Python 3.11)
- **Database**: PostgreSQL + pgvector
- **Search**: Meilisearch
- **Cache/Queue**: Redis
- **Workers**: Celery
- **Storage**: MinIO (S3-compatible)
- **Crawling**: Scrapy + Playwright
- **Frontend**: React 18 + TypeScript + Tailwind CSS + Vite
- **LLM Integration**: OpenAI, Anthropic, HuggingFace

### Design Patterns

The project implements several design patterns for maintainability:

- **Factory Pattern**: Crawler instantiation (Fast/JS mode)
- **Strategy Pattern**: Interchangeable SEO scoring algorithms
- **Command Pattern**: Crawl job encapsulation for replay
- **Repository Pattern**: Data access abstraction
- **Adapter Pattern**: LLM provider integration (OpenAI, Anthropic, HuggingFace)
- **Observer Pattern**: Event-based notifications
- **Circuit Breaker**: External API resilience

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Make (optional but recommended)

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/your-org/SEO-Tools.git
cd SEO-Tools
```

2. **Initialize the project**

```bash
make init
```

This will:
- Create `.env` file from template
- Build Docker containers
- Start core services
- Initialize the database

3. **Start the development environment**

```bash
make dev
```

4. **Access the application**

- **Frontend Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Backend API**: http://localhost:8000
- **Flower** (Celery monitoring): http://localhost:5555
- **Meilisearch**: http://localhost:7700
- **MinIO Console**: http://localhost:9001

### Manual Setup

If you prefer not to use Make:

```bash
# Copy environment file
cp backend/.env.example backend/.env

# Build containers
docker-compose build

# Start services
docker-compose up -d

# Apply database migrations
docker-compose exec backend alembic upgrade head
```

## Configuration

### Environment Variables

Edit `backend/.env` to configure:

```env
# Database
DATABASE_URL=postgresql://seouser:seopassword@postgres:5432/seosaas

# LLM Providers (Optional)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
HUGGINGFACE_API_KEY=hf_...

# Crawler Settings
CRAWLER_MAX_CONCURRENT=10
CRAWLER_DELAY=1.0
PLAYWRIGHT_HEADLESS=true
```

See `backend/.env.example` for all options.

## Usage

### API Examples

#### Create a Project

```bash
curl -X POST "http://localhost:8000/api/v1/projects/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Website",
    "domain": "https://example.com",
    "js_enabled": false,
    "max_depth": 3,
    "max_pages": 1000
  }'
```

#### Start a Crawl

```bash
curl -X POST "http://localhost:8000/api/v1/crawl/" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "mode": "fast",
    "config": {
      "depth": 3,
      "max_pages": 500
    }
  }'
```

#### Get Crawl Status

```bash
curl "http://localhost:8000/api/v1/crawl/1"
```

#### List Pages

```bash
curl "http://localhost:8000/api/v1/pages/?project_id=1&limit=50"
```

### Makefile Commands

```bash
make help          # Show all available commands
make up            # Start all services
make down          # Stop all services
make logs          # Show logs
make backend-shell # Open shell in backend container
make db-shell      # Open PostgreSQL shell
make test          # Run tests
make lint          # Run linter
make format        # Format code
make migrate       # Create new migration
make migrate-up    # Apply migrations
make clean         # Clean up containers and cache
```

## Development

### Project Structure

```
SEO-Tools/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   │   ├── endpoints/   # Route handlers
│   │   │   └── schemas/     # Pydantic schemas
│   │   ├── core/            # Config, database, Redis
│   │   ├── models/          # SQLAlchemy models
│   │   ├── repositories/    # Repository pattern
│   │   ├── services/        # Business logic
│   │   │   ├── crawler/     # Crawling services
│   │   │   ├── nlp/         # NLP & embeddings
│   │   │   └── llm/         # LLM integrations
│   │   ├── adapters/        # External service adapters
│   │   ├── workers/         # Celery tasks
│   │   └── main.py          # FastAPI app
│   ├── tests/               # Test suite
│   ├── migrations/          # Alembic migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                # React + TypeScript frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── lib/             # API client
│   │   └── types/           # TypeScript types
│   ├── Dockerfile
│   └── package.json
├── docs/                    # Documentation
├── scripts/                 # Utility scripts
├── docker-compose.yml
└── Makefile
```

### Adding a New Feature

1. Create model in `backend/app/models/`
2. Create repository in `backend/app/repositories/`
3. Create service in `backend/app/services/`
4. Create API schema in `backend/app/api/v1/schemas/`
5. Create endpoint in `backend/app/api/v1/endpoints/`
6. Add Celery task in `backend/app/workers/` if async
7. Write tests in `backend/tests/`
8. Create migration: `make migrate msg="Add feature"`
9. Apply migration: `make migrate-up`

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test
docker-compose exec backend pytest tests/test_projects.py
```

### Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Type check
make type-check
```

## API Documentation

Once the backend is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Roadmap

### Completed Features
- [x] Project structure and scaffold
- [x] Database models and migrations (PostgreSQL + pgvector)
- [x] API endpoints (Projects, Crawl, Pages, Usage, Content)
- [x] Docker Compose setup (Backend, Frontend, Celery, Redis, Postgres, Meilisearch, MinIO)
- [x] Celery workers for async tasks
- [x] Fast crawler (aiohttp-based)
- [x] JavaScript-enabled crawler (Playwright)
- [x] Repository pattern implementation
- [x] API key authentication
- [x] Rate limiting and quota management
- [x] Internal linking graph computation
- [x] Semantic similarity with embeddings (sentence-transformers)
- [x] Content generation (LLM integration: OpenAI, Anthropic, HuggingFace)
- [x] Frontend dashboard (React + TypeScript)
- [x] Multilingual support (French/English)
- [x] Comprehensive test suite (pytest)

### In Progress
- [ ] SERP analysis and competitor tracking
- [ ] Site tree/architecture generator with export
- [ ] Advanced Schema.org validation
- [ ] Webhook notifications system
- [ ] End-to-end testing

### Future Enhancements
- [ ] Advanced analytics and reporting
- [ ] Multi-tenant billing integration
- [ ] Keyword research tools
- [ ] Backlink analysis
- [ ] Performance monitoring
- [ ] Mobile SEO analysis

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Support

- Documentation: [docs/](./docs/)
- Issues: [GitHub Issues](https://github.com/your-org/SEO-Tools/issues)
- Email: support@example.com

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [PostgreSQL](https://www.postgresql.org/) + [pgvector](https://github.com/pgvector/pgvector)
- [Scrapy](https://scrapy.org/)
- [Playwright](https://playwright.dev/)
- [Celery](https://docs.celeryproject.org/)
- [Meilisearch](https://www.meilisearch.com/)
- [MinIO](https://min.io/)
