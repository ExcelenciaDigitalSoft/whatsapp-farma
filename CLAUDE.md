# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WhatsApp-based pharmacy billing and payment system with Clean Architecture implementation. Multi-tenant FastAPI application integrating WhatsApp (Chattigo), Mercado Pago payments, PostgreSQL (transactional data), MongoDB (chat history), and Redis (caching).

## Development Setup

### Prerequisites
- Python 3.11+
- Poetry (dependency management)
- Docker & Docker Compose (databases)

### Initial Setup
```bash
# Install dependencies (includes all groups: main, database, integrations, dev, test)
poetry install

# Install only production dependencies
poetry install --only main

# Activate virtual environment
poetry shell

# Start database services (PostgreSQL, MongoDB, Redis)
docker-compose up -d

# Copy environment variables
cp .env.example .env
# Edit .env with your credentials before running
```

### Database Migrations
```bash
# Generate new migration (after modifying SQLAlchemy models)
poetry run alembic revision --autogenerate -m "Description of changes"

# Apply pending migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1

# Check current migration version
poetry run alembic current

# View migration history
poetry run alembic history
```

### Running the Application
```bash
# Development mode with auto-reload (default port 3019)
poetry run uvicorn app.main:app --reload --port 3019

# Access interactive API documentation
# Swagger UI: http://localhost:3019/docs
# ReDoc: http://localhost:3019/redoc
```

## Testing Commands

### Running Tests
```bash
# All tests (147 tests total)
poetry run pytest

# By test type
poetry run pytest tests/unit/              # Unit tests (fast, ~1s)
poetry run pytest tests/integration/       # Integration tests (moderate, 5-10s)
poetry run pytest tests/e2e/              # E2E API tests (slower, 10-30s)

# Specific test file
poetry run pytest tests/unit/domain/value_objects/test_phone.py

# Specific test class
poetry run pytest tests/unit/domain/value_objects/test_phone.py::TestPhoneCreation

# Specific test method
poetry run pytest tests/unit/domain/value_objects/test_phone.py::TestPhoneCreation::test_create_with_full_international_format

# Pattern matching
poetry run pytest -k "test_phone"

# With coverage report
poetry run pytest --cov=app --cov-report=html --cov-report=term

# View HTML coverage report
open htmlcov/index.html

# Verbose output
poetry run pytest -v

# Show print statements
poetry run pytest -s

# Stop on first failure
poetry run pytest -x

# Re-run only failed tests
poetry run pytest --lf
```

### Test Structure
- **Unit Tests** (tests/unit/): Domain logic, value objects, entities, services, use cases with mocks
- **Integration Tests** (tests/integration/): Repository operations with SQLite in-memory database
- **E2E Tests** (tests/e2e/): Full HTTP API endpoints with test database

## Code Quality Tools

### Pre-commit Hooks
```bash
# Install git hooks
poetry run pre-commit install

# Run manually on all files
poetry run pre-commit run --all-files

# Or use setup script
chmod +x scripts/setup-quality-tools.sh
./scripts/setup-quality-tools.sh
```

### Individual Quality Checks
```bash
# Linting (Ruff - replaces flake8 + pylint)
poetry run ruff check .
poetry run ruff check --fix .

# Code formatting (Black)
poetry run black .
poetry run black --check .

# Import sorting (isort via Ruff)
poetry run ruff check --select I --fix .

# Type checking (mypy)
poetry run mypy app/

# Security analysis (Bandit)
poetry run bandit -r app/
```

## Clean Architecture Structure

The codebase follows Clean Architecture with strict layer separation and dependency inversion:

```
app/
├── domain/                    # Core business logic (no external dependencies)
│   ├── entities/             # Business entities (Client, Pharmacy, Transaction)
│   ├── value_objects/        # Immutable value objects (Phone, Money, ClientBalance, Email, TaxId, Address)
│   ├── services/             # Domain services (ClientValidator, TransactionNumberGenerator)
│   ├── interfaces/           # Repository and service interfaces (dependency inversion)
│   └── exceptions/           # Domain-specific exceptions
│
├── application/               # Use cases and orchestration
│   ├── use_cases/            # Business workflows (CreateClient, GetClient, CreateTransaction, ProcessPayment)
│   ├── dto/                  # Data Transfer Objects for use case I/O
│   └── interfaces/           # Use case interfaces
│
├── infrastructure/            # External concerns and implementations
│   ├── database/
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── repositories/    # Repository implementations (ClientRepository)
│   │   └── mappers/         # Entity ↔ Model mapping
│   ├── external/
│   │   ├── whatsapp/        # ChattigoAdapter (WhatsApp integration)
│   │   ├── payment/         # MercadoPagoAdapter (payment gateway)
│   │   └── ai/              # Optional AI integrations
│   ├── config/              # Configuration management (application, database, security, whatsapp, payment)
│   └── dependencies/        # DI container and FastAPI dependencies
│
├── presentation/              # HTTP/API layer (Clean Architecture endpoints)
│   ├── api/v1/              # Clean Architecture API endpoints
│   └── schemas/             # Pydantic request/response schemas
│
├── api/v1/                   # Legacy endpoints (gradual migration)
├── middleware/               # Auth, error handling
└── main.py                   # FastAPI application entry point
```

### Dependency Flow (Clean Architecture)
- **Domain** ← Application ← Infrastructure ← Presentation
- Domain has ZERO external dependencies (pure Python business logic)
- All dependencies point inward through interfaces
- Infrastructure implements domain interfaces
- Use Dependency Injection Container (app/infrastructure/dependencies/container.py)

### Key Design Patterns
- **Value Objects**: Immutable, validated objects (Phone normalizes to E.164, Money uses Decimal for precision)
- **Entities**: Identity-based objects with business rules (Client enforces credit limits)
- **Repository Pattern**: Abstract data access via interfaces
- **Use Case Pattern**: Single-responsibility business workflows
- **CQRS**: Separate read/write operations (CreateClientUseCase, GetClientUseCase)
- **Dependency Inversion**: Domain defines interfaces, Infrastructure implements them

## Adding New Features

### 1. Domain-First Approach
Start with domain layer (no external dependencies):
```python
# 1. Define value object if needed (app/domain/value_objects/)
# 2. Define or update entity (app/domain/entities/)
# 3. Define repository interface (app/domain/interfaces/repositories/)
# 4. Add domain validation rules to entity or domain service
```

### 2. Application Layer
```python
# 1. Create DTO for use case I/O (app/application/dto/)
# 2. Create use case (app/application/use_cases/)
# 3. Use repository interfaces (injected via constructor)
```

### 3. Infrastructure Layer
```python
# 1. Create/update SQLAlchemy model (app/infrastructure/database/models/)
# 2. Create mapper (app/infrastructure/database/mappers/)
# 3. Implement repository (app/infrastructure/database/repositories/)
# 4. Register in DI container (app/infrastructure/dependencies/)
```

### 4. Presentation Layer
```python
# 1. Create Pydantic schemas (app/presentation/schemas/)
# 2. Create endpoint (app/presentation/api/v1/)
# 3. Inject use case via FastAPI Depends()
```

### 5. Testing (TDD Recommended)
```python
# 1. Unit tests for domain (tests/unit/domain/)
# 2. Unit tests for use cases with mocks (tests/unit/application/)
# 3. Integration tests for repositories (tests/integration/)
# 4. E2E tests for API endpoints (tests/e2e/)
```

## Database Migrations Workflow

When modifying database schema:
1. Update SQLAlchemy model in `app/infrastructure/database/models/`
2. Generate migration: `poetry run alembic revision --autogenerate -m "Description"`
3. Review generated migration in `alembic/versions/`
4. Edit migration if needed (Alembic doesn't catch everything)
5. Test migration: `poetry run alembic upgrade head`
6. Add migration to git

## External Integrations

### WhatsApp (Chattigo)
- Adapter: `app/infrastructure/external/whatsapp/`
- Config: `CHATTIGO_API_URL`, `CHATTIGO_AUTH_TOKEN`, `CHATTIGO_WHATSAPP_NUMBER`
- Used for: Client notifications, chat history

### Mercado Pago (Payments)
- Adapter: `app/infrastructure/external/payment/`
- Config: `MERCADOPAGO_ACCESS_TOKEN`, `MERCADOPAGO_PUBLIC_KEY`
- Used for: Payment link generation, webhook processing

### Databases
- **PostgreSQL**: Transactional data (clients, transactions, invoices)
- **MongoDB**: Chat message history
- **Redis**: Caching and rate limiting

## Important Notes for AI

### Value Object Immutability
All value objects are immutable - use factory methods (`.create()`) for construction and return new instances for modifications.

### Phone Number Handling
- Always use `Phone.create()` for validation
- Normalizes to E.164 format (e.g., "+5491112345678")
- Stores both original and normalized versions

### Money Precision
- Use `Decimal` type, never `float` for money
- Create via `Money.create(amount, currency)` or `Money.zero(currency)`
- Supports arithmetic operations while maintaining immutability

### Multi-tenant Design
- All entities have `pharmacy_id` for tenant isolation
- Filter queries by pharmacy_id in repositories
- Enforce tenant isolation in use cases

### Testing Philosophy
- **Unit tests**: Fast, isolated, no I/O (mock repositories)
- **Integration tests**: Real database (SQLite in-memory), test repositories
- **E2E tests**: Full HTTP stack, test complete workflows
- Follow AAA pattern: Arrange, Act, Assert
- One logical assertion per test
- Use descriptive test names: `test_<scenario>_<expected_result>`

### Type Safety
- Use mypy for type checking: `poetry run mypy app/`
- All functions should have type hints
- Domain layer has strictest type checking
- Use Protocol for structural typing when appropriate

### Security Considerations
- Never commit `.env` with real credentials
- Use environment variables for all secrets
- Validate all external input via Pydantic schemas and domain value objects
- Implement RBAC through AuthMiddleware
- Rate limiting via Redis

## Commit Conventions

Follow conventional commits:
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation changes
- `style:` formatting, whitespace
- `refactor:` code restructuring
- `test:` add or update tests
- `chore:` maintenance tasks

## CI/CD Integration

Pre-commit hooks run:
- Black (formatting)
- Ruff (linting)
- mypy (type checking)
- Bandit (security scanning)
- Tests (unit tests only for speed)

Full test suite runs on PR and main branch pushes.
