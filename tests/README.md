# Testing Documentation

Comprehensive test suite for WhatsApp Pharmacy Assistant using Clean Architecture principles.

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures and configuration
├── unit/                       # Unit tests (fast, isolated)
│   ├── domain/
│   │   ├── value_objects/     # Value object tests
│   │   ├── entities/          # Entity tests
│   │   └── services/          # Domain service tests
│   └── application/
│       └── use_cases/         # Use case tests (with mocks)
├── integration/                # Integration tests (database, external services)
│   └── repositories/          # Repository integration tests
└── e2e/                        # End-to-end tests (full HTTP stack)
    └── api/                    # API endpoint tests

```

## Test Types

### Unit Tests
- **Location**: `tests/unit/`
- **Purpose**: Test individual components in isolation
- **Speed**: Very fast (< 1s total)
- **Dependencies**: No external dependencies, use mocks
- **Coverage Target**: 90%+

**Examples**:
- Value object validation and behavior
- Entity business logic
- Domain service logic
- Use case orchestration (with mocked repositories)

### Integration Tests
- **Location**: `tests/integration/`
- **Purpose**: Test component interactions with real infrastructure
- **Speed**: Moderate (5-10s)
- **Dependencies**: In-memory SQLite database
- **Coverage Target**: 80%+

**Examples**:
- Repository CRUD operations
- Database queries and filtering
- Data mapping and transformations

### E2E Tests
- **Location**: `tests/e2e/`
- **Purpose**: Test complete user workflows through HTTP API
- **Speed**: Slower (10-30s)
- **Dependencies**: Full application stack with test database
- **Coverage Target**: 70%+ for critical paths

**Examples**:
- API endpoint request/response validation
- Authentication and authorization
- Error handling and validation
- Multi-step business workflows

## Running Tests

### Quick Commands

```bash
# Run all tests
poetry run test

# Run with coverage report
poetry run pytest --cov=app --cov-report=html

# Run specific test type
poetry run pytest tests/unit/           # Unit tests only
poetry run pytest tests/integration/    # Integration tests only
poetry run pytest tests/e2e/           # E2E tests only

# Run specific test file
poetry run pytest tests/unit/domain/value_objects/test_phone.py

# Run specific test class
poetry run pytest tests/unit/domain/value_objects/test_phone.py::TestPhoneCreation

# Run specific test method
poetry run pytest tests/unit/domain/value_objects/test_phone.py::TestPhoneCreation::test_create_with_full_international_format

# Run tests matching pattern
poetry run pytest -k "test_phone"

# Run with verbose output
poetry run pytest -v

# Run with print statements visible
poetry run pytest -s

# Stop on first failure
poetry run pytest -x

# Run last failed tests
poetry run pytest --lf
```

### Watch Mode

```bash
# Install pytest-watch
poetry add --group dev pytest-watch

# Run tests on file change
poetry run ptw
```

## Test Configuration

Configuration is in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
minversion = "8.0"
addopts = ["-ra", "-q", "--strict-markers", "--strict-config", "--cov=app"]
testpaths = ["tests"]
pythonpath = ["."]
asyncio_mode = "auto"
```

## Writing Tests

### Unit Test Example

```python
"""Unit tests for Money value object."""
from decimal import Decimal
import pytest

from app.domain.value_objects.money import Money


class TestMoneyCreation:
    """Test money creation and validation."""

    def test_create_with_decimal(self):
        """Should create money with Decimal amount."""
        money = Money.create(Decimal("100.50"), "ARS")

        assert money.amount == Decimal("100.50")
        assert money.currency == "ARS"

    def test_create_with_negative_amount_raises_error(self):
        """Should raise error for negative amounts."""
        with pytest.raises(ValidationError, match="Amount cannot be negative"):
            Money.create(Decimal("-100"), "ARS")
```

### Integration Test Example

```python
"""Integration tests for ClientRepository."""
import pytest
from uuid import uuid4

from app.infrastructure.database.repositories.client_repository import ClientRepository


@pytest.mark.asyncio
class TestClientRepositoryCreate:
    """Test client repository create operations."""

    async def test_create_client(self, async_session):
        """Should create and persist client to database."""
        repository = ClientRepository(async_session)

        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(Money.zero("ARS"), Money.zero("ARS"))
        )

        created_client = await repository.create(client)

        assert created_client.id is not None
```

### E2E Test Example

```python
"""End-to-end tests for Client API endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestCreateClientEndpoint:
    """Test POST /api/v1/clients/ endpoint."""

    async def test_create_client_success(self, test_client):
        """Should create client and return 201."""
        request_data = {
            "pharmacy_id": str(uuid4()),
            "phone": "+54 9 11 1234 5678",
            "first_name": "Juan"
        }

        response = await test_client.post("/api/v1/clients/", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["phone"] == "+54 9 11 1234 5678"
```

## Fixtures

Common fixtures are defined in `tests/conftest.py`:

### Database Fixtures
- `async_engine`: Test database engine (SQLite in-memory)
- `async_session`: Test database session (function-scoped)

### Domain Fixtures
- `sample_phone`: Phone value object
- `sample_money`: Money value object
- `sample_balance`: ClientBalance value object
- `sample_client`: Client entity
- `sample_pharmacy`: Pharmacy entity

### Mock Fixtures
- `mock_client_repository`: Mocked client repository
- `mock_transaction_repository`: Mocked transaction repository
- `mock_notification_service`: Mocked WhatsApp service
- `mock_payment_gateway`: Mocked payment gateway

## Best Practices

### Test Naming
- **Class**: `Test<ComponentName><TestType>` (e.g., `TestPhoneCreation`)
- **Method**: `test_<scenario>_<expected_result>` (e.g., `test_create_with_invalid_phone_raises_error`)

### Test Structure (AAA Pattern)
```python
async def test_something(self):
    """Should do something when condition."""
    # Arrange - Setup test data
    client = create_test_client()

    # Act - Execute the behavior
    result = await use_case.execute(command)

    # Assert - Verify expectations
    assert result.status == "active"
```

### Docstrings
- Every test should have a docstring explaining what it tests
- Use imperative mood: "Should create..." not "Creates..."

### Assertions
- One logical assertion per test (can have multiple assert statements for same concept)
- Use descriptive assertion messages for complex checks
- Prefer `pytest.raises()` for exception testing

### Test Independence
- Each test should be completely independent
- Use fixtures for setup, not shared state
- Clean up resources in fixtures with yield
- Avoid test order dependencies

### Async Tests
- Mark async tests with `@pytest.mark.asyncio`
- Use `async def` for test methods
- Use `await` for async operations
- Use `AsyncMock` for mocking async methods

## Coverage Goals

| Layer | Target Coverage | Current |
|-------|----------------|---------|
| Domain (Value Objects) | 95%+ | ✅ |
| Domain (Entities) | 90%+ | ✅ |
| Domain (Services) | 90%+ | ✅ |
| Application (Use Cases) | 85%+ | ✅ |
| Infrastructure (Repositories) | 80%+ | ✅ |
| Presentation (API) | 75%+ | ✅ |
| **Overall** | **85%+** | 🎯 |

## Coverage Reports

Generate HTML coverage report:

```bash
poetry run pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## CI/CD Integration

Tests run automatically on:
- Every commit (pre-commit hooks for fast tests)
- Pull requests (full test suite)
- Main branch pushes (full suite with coverage)

## Troubleshooting

### Tests are slow
- Run only unit tests: `pytest tests/unit/`
- Use `pytest -x` to stop on first failure
- Check for unnecessary database operations
- Use mocks instead of real dependencies

### Database conflicts
- Each test should use isolated session
- Ensure fixtures properly clean up
- Check for transaction rollbacks

### Import errors
- Ensure virtual environment is activated
- Run `poetry install --with test`
- Check PYTHONPATH includes project root

### Async test errors
- Ensure `@pytest.mark.asyncio` decorator
- Use `AsyncMock` for async methods
- Check `asyncio_mode = "auto"` in pytest config

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
- [Clean Architecture Testing](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
