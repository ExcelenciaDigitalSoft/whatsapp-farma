"""Pytest configuration and shared fixtures."""
import asyncio
from datetime import datetime
from decimal import Decimal
from typing import AsyncGenerator, Generator
from uuid import UUID, uuid4

import pytest  # type: ignore

# Only import domain objects, not infrastructure
from app.domain.value_objects.phone import Phone
from app.domain.value_objects.money import Money
from app.domain.value_objects.client_balance import ClientBalance
from app.domain.value_objects.address import Address
from app.domain.value_objects.email import Email
from app.domain.value_objects.tax_id import TaxId
from app.domain.entities.client import Client
from app.domain.entities.pharmacy import Pharmacy


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Database fixtures for integration tests only
@pytest.fixture(scope="function")
async def async_engine():
    """Create a test database engine (for integration tests)."""
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool

    TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Import Base only when needed
    try:
        from app.infrastructure.database.models.base import Base  # type: ignore

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield engine

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    except ImportError:
        # Base models not yet implemented, skip database setup
        yield engine

    await engine.dispose()


@pytest.fixture(scope="function")
async def async_session(async_engine) -> AsyncGenerator:
    """Create a test database session (for integration tests)."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    async_session_maker = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:  # type: ignore
        yield session


# ==================== Domain Fixtures ====================

@pytest.fixture
def sample_phone() -> Phone:
    """Create a sample phone value object."""
    return Phone.create("+54 9 11 1234 5678")


@pytest.fixture
def sample_money() -> Money:
    """Create a sample money value object."""
    return Money.create(Decimal("1000.00"), "ARS")


@pytest.fixture
def sample_balance() -> ClientBalance:
    """Create a sample client balance."""
    return ClientBalance.create(
        current_balance=Money.zero("ARS"),
        credit_limit=Money.create(Decimal("5000.00"), "ARS")
    )


@pytest.fixture
def sample_address() -> Address:
    """Create a sample address value object."""
    return Address.create(
        street="Av. Corrientes 1234",
        city="Buenos Aires",
        state="CABA",
        postal_code="C1043",
        country="AR"
    )


@pytest.fixture
def sample_pharmacy_id() -> UUID:
    """Create a sample pharmacy UUID."""
    return uuid4()


@pytest.fixture
def sample_client_id() -> UUID:
    """Create a sample client UUID."""
    return uuid4()


@pytest.fixture
def sample_pharmacy(sample_pharmacy_id: UUID) -> Pharmacy:
    """Create a sample pharmacy entity."""
    return Pharmacy(
        id=sample_pharmacy_id,
        name="Farmacia Test",
        tax_id=TaxId.create("20-12345678-9", "CUIT"),
        phone=Phone.create("+54 11 4444 5555"),
        email=Email.create("farmacia@test.com"),
        address=Address.create(
            street="Av. Test 123",
            city="Buenos Aires",
            state="CABA",
            postal_code="C1000",
            country="AR"
        ),
        status="active",
        subscription_plan="premium",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_client(
    sample_client_id: UUID,
    sample_pharmacy_id: UUID,
    sample_phone: Phone,
    sample_balance: ClientBalance
) -> Client:
    """Create a sample client entity."""
    return Client(
        id=sample_client_id,
        pharmacy_id=sample_pharmacy_id,
        phone=sample_phone,
        first_name="Juan",
        last_name="Pérez",
        email=Email.create("juan@example.com"),
        balance=sample_balance,
        status="active",
        whatsapp_opted_in=True,
        tags=["vip", "mayorista"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


# ==================== Mock Fixtures ====================

@pytest.fixture
def mock_client_repository():
    """Create a mock client repository."""
    from unittest.mock import AsyncMock

    repository = AsyncMock()
    repository.create = AsyncMock()
    repository.find_by_id = AsyncMock()
    repository.find_by_phone = AsyncMock()
    repository.update = AsyncMock()
    repository.delete = AsyncMock()

    return repository


@pytest.fixture
def mock_transaction_repository():
    """Create a mock transaction repository."""
    from unittest.mock import AsyncMock

    repository = AsyncMock()
    repository.create = AsyncMock()
    repository.find_by_id = AsyncMock()
    repository.get_next_sequence_number = AsyncMock(return_value=1)

    return repository


@pytest.fixture
def mock_notification_service():
    """Create a mock notification service."""
    from unittest.mock import AsyncMock

    service = AsyncMock()
    service.send_message = AsyncMock(return_value=True)
    service.send_template = AsyncMock(return_value=True)

    return service


@pytest.fixture
def mock_payment_gateway():
    """Create a mock payment gateway."""
    from unittest.mock import AsyncMock

    gateway = AsyncMock()
    gateway.create_payment = AsyncMock(return_value={
        "payment_id": "test_payment_123",
        "payment_url": "https://test.mercadopago.com/checkout/123"
    })
    gateway.get_payment_status = AsyncMock(return_value="approved")

    return gateway
