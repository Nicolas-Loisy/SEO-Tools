# Contributing to SEO SaaS Tool

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Getting Started

1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/SEO-Tools.git
   cd SEO-Tools
   ```

2. **Set up development environment**
   ```bash
   make init
   ```

3. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Code Style

We use automated formatting and linting:

- **Python**: Black (formatting), Ruff (linting), MyPy (type checking)
- **Line length**: 100 characters
- **Target**: Python 3.11+

Format your code before committing:

```bash
make format
make lint
make type-check
```

### Testing

Write tests for all new features:

```bash
# Run tests
make test

# Run with coverage
make test-cov
```

Tests should be placed in `backend/tests/` and follow the naming convention `test_*.py`.

### Commit Messages

Follow conventional commits:

```
feat: add new crawler mode
fix: resolve database connection issue
docs: update API documentation
test: add tests for project endpoints
refactor: simplify crawler factory
chore: update dependencies
```

## Project Structure

- **backend/app/api/**: API endpoints and schemas
- **backend/app/core/**: Core configuration and database
- **backend/app/models/**: SQLAlchemy ORM models
- **backend/app/repositories/**: Data access layer (Repository pattern)
- **backend/app/services/**: Business logic
- **backend/app/workers/**: Celery tasks
- **backend/tests/**: Test suite

## Design Patterns

When adding new features, follow established patterns:

### Repository Pattern

```python
class MyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, obj: MyModel) -> MyModel:
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get_by_id(self, id: int) -> Optional[MyModel]:
        result = await self.db.execute(
            select(MyModel).where(MyModel.id == id)
        )
        return result.scalar_one_or_none()
```

### Factory Pattern

```python
class ServiceFactory:
    @staticmethod
    def create(type: str, config: dict) -> BaseService:
        if type == "type_a":
            return ServiceA(config)
        elif type == "type_b":
            return ServiceB(config)
        raise ValueError(f"Unknown service type: {type}")
```

### Adapter Pattern

```python
class ExternalServiceAdapter(ABC):
    @abstractmethod
    def perform_action(self, data: dict) -> Result:
        pass

class ProviderAAdapter(ExternalServiceAdapter):
    def perform_action(self, data: dict) -> Result:
        # Implementation
        pass
```

## Database Migrations

When changing models:

```bash
# Create migration
make migrate msg="Add new field to Project"

# Review the generated migration
# Edit backend/migrations/versions/XXXXXX_add_new_field_to_project.py if needed

# Apply migration
make migrate-up
```

## API Endpoints

When adding new endpoints:

1. **Create Pydantic schema** in `app/api/v1/schemas/`
2. **Add endpoint** in `app/api/v1/endpoints/`
3. **Include router** in `app/api/v1/__init__.py`
4. **Write tests** in `backend/tests/`
5. **Update API docs** in `docs/API.md`

Example:

```python
# app/api/v1/schemas/my_resource.py
class MyResourceCreate(BaseModel):
    name: str
    value: int

class MyResourceResponse(BaseModel):
    id: int
    name: str
    value: int

    class Config:
        from_attributes = True

# app/api/v1/endpoints/my_resource.py
@router.post("/", response_model=MyResourceResponse)
async def create_resource(
    data: MyResourceCreate,
    db: AsyncSession = Depends(get_db),
):
    resource = MyResource(**data.model_dump())
    db.add(resource)
    await db.commit()
    await db.refresh(resource)
    return resource
```

## Celery Tasks

When adding async tasks:

1. **Create task** in `app/workers/`
2. **Import task** in `app/workers/celery_app.py`
3. **Add queue route** in Celery config if needed
4. **Write tests** using `@patch` for Celery

Example:

```python
# app/workers/my_tasks.py
from app.workers.celery_app import celery_app

@celery_app.task(name="app.workers.my_tasks.process_data")
def process_data(data_id: int) -> dict:
    # Process data
    return {"status": "success"}
```

## Documentation

- Update `README.md` for user-facing changes
- Update `docs/API.md` for API changes
- Update `docs/ARCHITECTURE.md` for architectural changes
- Add docstrings to all functions/classes

## Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new features
3. **Ensure all tests pass**: `make test`
4. **Format code**: `make format`
5. **Lint code**: `make lint`
6. **Update CHANGELOG** (if exists)
7. **Create PR** with clear description

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added new tests
- [ ] Updated documentation

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added where needed
- [ ] Documentation updated
```

## Code Review

All submissions require review. We use GitHub pull requests for this purpose.

Reviewers will check:
- Code quality and style
- Test coverage
- Documentation
- Performance implications
- Security considerations

## Questions?

Open an issue or join our discussion forum.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
