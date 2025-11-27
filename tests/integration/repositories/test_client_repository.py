"""Integration tests for ClientRepository."""
from decimal import Decimal
from uuid import uuid4

import pytest  # type: ignore

from app.infrastructure.database.repositories.client_repository import ClientRepository
from app.domain.entities.client import Client
from app.domain.value_objects.phone import Phone
from app.domain.value_objects.money import Money
from app.domain.value_objects.client_balance import ClientBalance
from app.domain.value_objects.email import Email


@pytest.mark.asyncio
class TestClientRepositoryCreate:
    """Test client repository create operations."""

    async def test_create_client(self, async_session):
        """Should create and persist client to database."""
        # Arrange
        repository = ClientRepository(async_session)
        pharmacy_id = uuid4()

        client = Client(
            pharmacy_id=pharmacy_id,
            phone=Phone.create("+54 9 11 1234 5678"),
            first_name="Juan",
            last_name="Pérez",
            email=Email.create("juan@example.com"),
            balance=ClientBalance.create(
                Money.zero("ARS"),
                Money.create(Decimal("5000.00"), "ARS")
            )
        )

        # Act
        created_client = await repository.create(client)

        # Assert
        assert created_client.id is not None
        assert created_client.pharmacy_id == pharmacy_id
        assert created_client.phone.normalized == "+5491112345678"
        assert created_client.first_name == "Juan"
        assert created_client.last_name == "Pérez"
        assert created_client.balance.credit_limit.amount == Decimal("5000.00")

    async def test_create_client_with_minimal_data(self, async_session):
        """Should create client with only required fields."""
        repository = ClientRepository(async_session)
        pharmacy_id = uuid4()

        client = Client(
            pharmacy_id=pharmacy_id,
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(Money.zero("ARS"), Money.zero("ARS"))
        )

        created_client = await repository.create(client)

        assert created_client.id is not None
        assert created_client.first_name is None
        assert created_client.last_name is None


@pytest.mark.asyncio
class TestClientRepositoryFindById:
    """Test find client by ID."""

    async def test_find_by_id_existing_client(self, async_session):
        """Should find client by ID."""
        repository = ClientRepository(async_session)
        pharmacy_id = uuid4()

        # Create client
        client = Client(
            pharmacy_id=pharmacy_id,
            phone=Phone.create("+54 9 11 1234 5678"),
            first_name="Test",
            balance=ClientBalance.create(Money.zero("ARS"), Money.zero("ARS"))
        )
        created = await repository.create(client)

        # Find by ID
        found = await repository.find_by_id(created.id)

        assert found is not None
        assert found.id == created.id
        assert found.first_name == "Test"

    async def test_find_by_id_non_existent(self, async_session):
        """Should return None for non-existent client."""
        repository = ClientRepository(async_session)

        found = await repository.find_by_id(uuid4())

        assert found is None


@pytest.mark.asyncio
class TestClientRepositoryFindByPhone:
    """Test find client by phone number."""

    async def test_find_by_phone_existing(self, async_session):
        """Should find client by phone number."""
        repository = ClientRepository(async_session)
        pharmacy_id = uuid4()
        phone = Phone.create("+54 9 11 1234 5678")

        # Create client
        client = Client(
            pharmacy_id=pharmacy_id,
            phone=phone,
            balance=ClientBalance.create(Money.zero("ARS"), Money.zero("ARS"))
        )
        await repository.create(client)

        # Find by phone
        found = await repository.find_by_phone(phone, pharmacy_id)

        assert found is not None
        assert found.phone.normalized == phone.normalized
        assert found.pharmacy_id == pharmacy_id

    async def test_find_by_phone_different_format_same_normalized(self, async_session):
        """Should find client even with different phone format."""
        repository = ClientRepository(async_session)
        pharmacy_id = uuid4()

        # Create with one format
        client = Client(
            pharmacy_id=pharmacy_id,
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(Money.zero("ARS"), Money.zero("ARS"))
        )
        await repository.create(client)

        # Search with different format
        search_phone = Phone.create("54-9-11-1234-5678")
        found = await repository.find_by_phone(search_phone, pharmacy_id)

        assert found is not None

    async def test_find_by_phone_wrong_pharmacy(self, async_session):
        """Should not find client from different pharmacy."""
        repository = ClientRepository(async_session)
        pharmacy_id_1 = uuid4()
        pharmacy_id_2 = uuid4()
        phone = Phone.create("+54 9 11 1234 5678")

        # Create client for pharmacy 1
        client = Client(
            pharmacy_id=pharmacy_id_1,
            phone=phone,
            balance=ClientBalance.create(Money.zero("ARS"), Money.zero("ARS"))
        )
        await repository.create(client)

        # Search in pharmacy 2
        found = await repository.find_by_phone(phone, pharmacy_id_2)

        assert found is None

    async def test_find_by_phone_non_existent(self, async_session):
        """Should return None for non-existent phone."""
        repository = ClientRepository(async_session)

        found = await repository.find_by_phone(
            Phone.create("+54 9 11 9999 9999"),
            uuid4()
        )

        assert found is None


@pytest.mark.asyncio
class TestClientRepositoryUpdate:
    """Test client repository update operations."""

    async def test_update_client(self, async_session):
        """Should update client data."""
        repository = ClientRepository(async_session)
        pharmacy_id = uuid4()

        # Create client
        client = Client(
            pharmacy_id=pharmacy_id,
            phone=Phone.create("+54 9 11 1234 5678"),
            first_name="Original",
            balance=ClientBalance.create(Money.zero("ARS"), Money.zero("ARS"))
        )
        created = await repository.create(client)

        # Update
        created.first_name = "Updated"
        created.last_name = "Name"
        updated = await repository.update(created.id, created)

        # Verify
        assert updated is not None
        assert updated.first_name == "Updated"
        assert updated.last_name == "Name"

        # Verify persistence
        found = await repository.find_by_id(created.id)
        assert found is not None
        assert found.first_name == "Updated"


@pytest.mark.asyncio
class TestClientRepositoryFindByPharmacy:
    """Test finding clients by pharmacy."""

    async def test_find_by_pharmacy_multiple_clients(self, async_session):
        """Should find all clients for a pharmacy."""
        repository = ClientRepository(async_session)
        pharmacy_id = uuid4()

        # Create multiple clients
        for i in range(3):
            client = Client(
                pharmacy_id=pharmacy_id,
                phone=Phone.create(f"+54 9 11 1234 567{i}"),
                balance=ClientBalance.create(Money.zero("ARS"), Money.zero("ARS"))
            )
            await repository.create(client)

        # Find all
        clients = await repository.find_by_pharmacy(pharmacy_id)

        assert len(clients) == 3

    async def test_find_by_pharmacy_with_pagination(self, async_session):
        """Should respect pagination parameters."""
        repository = ClientRepository(async_session)
        pharmacy_id = uuid4()

        # Create 5 clients
        for i in range(5):
            client = Client(
                pharmacy_id=pharmacy_id,
                phone=Phone.create(f"+54 9 11 1234 567{i}"),
                balance=ClientBalance.create(Money.zero("ARS"), Money.zero("ARS"))
            )
            await repository.create(client)

        # Get first page
        page1 = await repository.find_by_pharmacy(pharmacy_id, skip=0, limit=2)
        assert len(page1) == 2

        # Get second page
        page2 = await repository.find_by_pharmacy(pharmacy_id, skip=2, limit=2)
        assert len(page2) == 2

        # Verify different clients
        page1_ids = {c.id for c in page1}
        page2_ids = {c.id for c in page2}
        assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.asyncio
class TestClientRepositoryFindWithDebt:
    """Test finding clients with debt."""

    async def test_find_with_debt_filters_correctly(self, async_session):
        """Should only return clients with negative balance."""
        repository = ClientRepository(async_session)
        pharmacy_id = uuid4()

        # Client with debt
        client_with_debt = Client(
            pharmacy_id=pharmacy_id,
            phone=Phone.create("+54 9 11 1234 5671"),
            balance=ClientBalance(
                current_balance=Money(amount=Decimal("-1000"), currency="ARS"),
                credit_limit=Money.create(Decimal("5000"), "ARS")
            )
        )
        await repository.create(client_with_debt)

        # Client without debt
        client_no_debt = Client(
            pharmacy_id=pharmacy_id,
            phone=Phone.create("+54 9 11 1234 5672"),
            balance=ClientBalance.create(Money.zero("ARS"), Money.zero("ARS"))
        )
        await repository.create(client_no_debt)

        # Find clients with debt
        clients_with_debt = await repository.find_with_debt(pharmacy_id)

        assert len(clients_with_debt) == 1
        assert clients_with_debt[0].owes_money


@pytest.mark.asyncio
class TestClientRepositorySearch:
    """Test client search functionality."""

    async def test_search_by_name(self, async_session):
        """Should find clients matching name search."""
        repository = ClientRepository(async_session)
        pharmacy_id = uuid4()

        # Create clients
        client1 = Client(
            pharmacy_id=pharmacy_id,
            phone=Phone.create("+54 9 11 1234 5671"),
            first_name="Juan",
            last_name="Pérez",
            balance=ClientBalance.create(Money.zero("ARS"), Money.zero("ARS"))
        )
        await repository.create(client1)

        client2 = Client(
            pharmacy_id=pharmacy_id,
            phone=Phone.create("+54 9 11 1234 5672"),
            first_name="María",
            last_name="González",
            balance=ClientBalance.create(Money.zero("ARS"), Money.zero("ARS"))
        )
        await repository.create(client2)

        # Search for "Juan"
        results = await repository.search("Juan", pharmacy_id)

        assert len(results) == 1
        assert results[0].first_name == "Juan"

    async def test_search_by_phone_partial(self, async_session):
        """Should find clients by partial phone match."""
        repository = ClientRepository(async_session)
        pharmacy_id = uuid4()

        client = Client(
            pharmacy_id=pharmacy_id,
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(Money.zero("ARS"), Money.zero("ARS"))
        )
        await repository.create(client)

        # Search by partial phone
        results = await repository.search("1234", pharmacy_id)

        assert len(results) >= 1


@pytest.mark.asyncio
class TestClientRepositoryDelete:
    """Test client deletion (soft delete)."""

    async def test_delete_client_soft(self, async_session):
        """Should soft delete client (set status to inactive)."""
        repository = ClientRepository(async_session)
        pharmacy_id = uuid4()

        client = Client(
            pharmacy_id=pharmacy_id,
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(Money.zero("ARS"), Money.zero("ARS")),
            status="active"
        )
        created = await repository.create(client)

        # Delete
        await repository.delete(created.id)

        # Verify still in DB but inactive
        found = await repository.find_by_id(created.id)
        assert found is not None
        assert found.status == "inactive"
