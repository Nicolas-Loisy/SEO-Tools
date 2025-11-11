# Tests

## Overview

Comprehensive test suite for SEO SaaS Tool with unit, integration, and end-to-end tests.

## Structure

```
tests/
├── conftest.py           # Pytest fixtures and configuration
├── unit/                 # Unit tests (isolated components)
│   ├── services/        # Service layer tests
│   ├── api/             # API endpoint tests
│   └── models/          # Model tests
├── integration/          # Integration tests (multiple components)
└── e2e/                  # End-to-end tests (full workflows)
```

## Running Tests

### All Tests

```bash
# From backend directory
pytest

# With coverage
pytest --cov=app --cov-report=html --cov-report=term

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Specific Test Types

```bash
# Unit tests only
pytest tests/unit -m unit

# Integration tests
pytest tests/integration -m integration

# Slow tests excluded
pytest -m "not slow"
```

### Single Test File

```bash
pytest tests/unit/services/test_rate_limit.py

# Single test function
pytest tests/unit/services/test_rate_limit.py::test_check_and_increment_within_limit
```

## Writing Tests

### Unit Test Example

```python
import pytest
from app.services.my_service import MyService


def test_my_function():
    """Test my function with valid input."""
    # Arrange
    service = MyService()
    
    # Act
    result = service.my_function(input_data)
    
    # Assert
    assert result == expected_value


@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    service = MyService()
    result = await service.async_function()
    assert result is not None
```

### Integration Test Example

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_workflow(db_session):
    """Test complete workflow."""
    # Setup
    project = Project(name="Test", domain="https://test.com")
    db_session.add(project)
    await db_session.commit()
    
    # Execute workflow
    result = await run_workflow(project.id)
    
    # Verify
    assert result.status == "completed"
```

## Test Fixtures

Available fixtures from `conftest.py`:

- `db_session`: Database session for tests
- `client`: HTTP client for API tests
- `test_engine`: Test database engine
- `sample_page_data`: Sample page data
- `sample_project_data`: Sample project data
- `sample_tenant_data`: Sample tenant data

## Mocking

### Mock External Services

```python
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_with_mock():
    """Test with mocked external service."""
    with patch('app.services.external.api_call') as mock_call:
        mock_call.return_value = {"status": "success"}
        
        result = await my_function()
        assert result == "success"
```

## Coverage

### Generate Coverage Report

```bash
pytest --cov=app --cov-report=html

# Open in browser
open htmlcov/index.html
```

### Coverage Goals

- Overall: > 80%
- Critical services: > 90%
- API endpoints: > 85%

## CI/CD Integration

Tests run automatically on:
- Every commit
- Pull requests
- Before deployment

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          docker-compose up -d postgres redis
          pytest --cov=app
```

## Best Practices

1. **Arrange-Act-Assert**: Structure tests clearly
2. **One assertion per test**: Focus on single behavior
3. **Descriptive names**: Test names should explain what is tested
4. **Independent tests**: No dependencies between tests
5. **Fast tests**: Keep unit tests under 1 second
6. **Clean up**: Use fixtures for setup/teardown
7. **Mock external calls**: Don't call real APIs in tests

## Debugging Tests

```bash
# Print output
pytest -s

# Drop into debugger on failure
pytest --pdb

# Last failed tests only
pytest --lf

# Verbose output
pytest -vv
```

## Performance Testing

```bash
# Show slowest tests
pytest --durations=10

# Profile tests
pytest --profile
```

## Test Database

Tests use a separate `seosaas_test` database to avoid affecting development data.

### Setup Test Database

```bash
docker-compose exec postgres psql -U seouser -c "CREATE DATABASE seosaas_test;"
```

## Continuous Testing

```bash
# Watch mode (requires pytest-watch)
ptw

# With coverage
ptw -- --cov=app
```
