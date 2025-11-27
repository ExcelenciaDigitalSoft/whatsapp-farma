"""Unit tests for CreateClientUseCase."""
from decimal import Decimal
from uuid import uuid4

import pytest  # type: ignore
from unittest.mock import AsyncMock

from app.application.use_cases.create_client import CreateClientUseCase
from app.application.dto.client_dto import CreateClientDTO
from app.domain.entities.client import Client
from app.domain.value_objects.phone import Phone
from app.domain.value_objects.money import Money
from app.domain.value_objects.client_balance import ClientBalance
from app.domain.value_objects.email import Email
from app.domain.exceptions import DuplicateEntityError, ValidationError


@pytest.mark.asyncio
class TestCreateClientUseCase:
    """Test CreateClientUseCase."""

    async def test_create_client_success(self, mock_client_repository):
        """Should create client successfully."""
        # Arrange
        pharmacy_id = uuid4()
        command = CreateClientDTO(
            pharmacy_id=pharmacy_id,
            phone="+54 9 11 1234 5678",
            first_name="Juan",
            last_name="Pérez",
            email="juan@example.com",
            credit_limit=Decimal("5000.00")
        )

        expected_client = Client(
            id=uuid4(),
            pharmacy_id=pharmacy_id,
            phone=Phone.create("+54 9 11 1234 5678"),
            first_name="Juan",
            last_name="Pérez",
            email=Email.create("juan@example.com"),
            balance=ClientBalance.create(
                Money.zero("ARS"),
                Money.create(Decimal("5000.00"), "ARS")
            ),
            status="active"
        )

        mock_client_repository.find_by_phone.return_value = None
        mock_client_repository.create.return_value = expected_client

        use_case = CreateClientUseCase(client_repository=mock_client_repository)

        # Act
        result = await use_case.execute(command)

        # Assert
        assert result.id == expected_client.id
        assert result.phone == "+54 9 11 1234 5678"
        assert result.phone_normalized == "+5491112345678"
        assert result.first_name == "Juan"
        assert result.last_name == "Pérez"
        assert result.email == "juan@example.com"
        assert result.credit_limit == Decimal("5000.00")
        assert result.current_balance == Decimal("0")
        assert result.available_credit == Decimal("5000.00")

        # Verify repository calls
        mock_client_repository.find_by_phone.assert_called_once()
        mock_client_repository.create.assert_called_once()

    async def test_create_client_with_minimal_data(self, mock_client_repository):
        """Should create client with only required fields."""
        pharmacy_id = uuid4()
        command = CreateClientDTO(
            pharmacy_id=pharmacy_id,
            phone="+54 9 11 1234 5678"
        )

        expected_client = Client(
            id=uuid4(),
            pharmacy_id=pharmacy_id,
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(
                Money.zero("ARS"),
                Money.zero("ARS")
            )
        )

        mock_client_repository.find_by_phone.return_value = None
        mock_client_repository.create.return_value = expected_client

        use_case = CreateClientUseCase(client_repository=mock_client_repository)

        # Act
        result = await use_case.execute(command)

        # Assert
        assert result.id == expected_client.id
        assert result.phone == "+54 9 11 1234 5678"
        assert result.credit_limit == Decimal("0")

    async def test_create_client_duplicate_phone_raises_error(self, mock_client_repository):
        """Should raise error when client with phone already exists."""
        pharmacy_id = uuid4()
        command = CreateClientDTO(
            pharmacy_id=pharmacy_id,
            phone="+54 9 11 1234 5678"
        )

        existing_client = Client(
            id=uuid4(),
            pharmacy_id=pharmacy_id,
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(Money.zero("ARS"), Money.zero("ARS"))
        )

        mock_client_repository.find_by_phone.return_value = existing_client

        use_case = CreateClientUseCase(client_repository=mock_client_repository)

        # Act & Assert
        with pytest.raises(DuplicateEntityError, match="Client.*phone.*already exists"):
            await use_case.execute(command)

        # Should not attempt to create
        mock_client_repository.create.assert_not_called()

    async def test_create_client_invalid_phone_raises_error(self, mock_client_repository):
        """Should raise error for invalid phone number."""
        command = CreateClientDTO(
            pharmacy_id=uuid4(),
            phone="invalid-phone"
        )

        use_case = CreateClientUseCase(client_repository=mock_client_repository)

        # Act & Assert
        with pytest.raises(ValidationError):
            await use_case.execute(command)

    async def test_create_client_normalizes_phone(self, mock_client_repository):
        """Should normalize phone number before checking duplicates."""
        pharmacy_id = uuid4()
        command = CreateClientDTO(
            pharmacy_id=pharmacy_id,
            phone="54-9-11-1234-5678"  # Different format
        )

        expected_client = Client(
            id=uuid4(),
            pharmacy_id=pharmacy_id,
            phone=Phone.create("54-9-11-1234-5678"),
            balance=ClientBalance.create(Money.zero("ARS"), Money.zero("ARS"))
        )

        mock_client_repository.find_by_phone.return_value = None
        mock_client_repository.create.return_value = expected_client

        use_case = CreateClientUseCase(client_repository=mock_client_repository)

        # Act
        result = await use_case.execute(command)

        # Assert
        assert result.phone_normalized == "+5491112345678"

        # Verify phone was normalized when checking duplicates
        call_args = mock_client_repository.find_by_phone.call_args
        called_phone = call_args[0][0]
        assert called_phone.normalized == "+5491112345678"

    async def test_create_client_with_tags(self, mock_client_repository):
        """Should create client with tags."""
        pharmacy_id = uuid4()
        command = CreateClientDTO(
            pharmacy_id=pharmacy_id,
            phone="+54 9 11 1234 5678",
            tags=["vip", "mayorista"]
        )

        expected_client = Client(
            id=uuid4(),
            pharmacy_id=pharmacy_id,
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(Money.zero("ARS"), Money.zero("ARS")),
            tags=["vip", "mayorista"]
        )

        mock_client_repository.find_by_phone.return_value = None
        mock_client_repository.create.return_value = expected_client

        use_case = CreateClientUseCase(client_repository=mock_client_repository)

        # Act
        result = await use_case.execute(command)

        # Assert
        assert "vip" in result.tags
        assert "mayorista" in result.tags

    async def test_create_client_sets_default_status_active(self, mock_client_repository):
        """Should set default status to active."""
        pharmacy_id = uuid4()
        command = CreateClientDTO(
            pharmacy_id=pharmacy_id,
            phone="+54 9 11 1234 5678"
        )

        expected_client = Client(
            id=uuid4(),
            pharmacy_id=pharmacy_id,
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(Money.zero("ARS"), Money.zero("ARS")),
            status="active"
        )

        mock_client_repository.find_by_phone.return_value = None
        mock_client_repository.create.return_value = expected_client

        use_case = CreateClientUseCase(client_repository=mock_client_repository)

        # Act
        result = await use_case.execute(command)

        # Assert
        assert result.status == "active"

    async def test_create_client_with_zero_credit_limit(self, mock_client_repository):
        """Should allow zero credit limit."""
        pharmacy_id = uuid4()
        command = CreateClientDTO(
            pharmacy_id=pharmacy_id,
            phone="+54 9 11 1234 5678",
            credit_limit=Decimal("0")
        )

        expected_client = Client(
            id=uuid4(),
            pharmacy_id=pharmacy_id,
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(Money.zero("ARS"), Money.zero("ARS"))
        )

        mock_client_repository.find_by_phone.return_value = None
        mock_client_repository.create.return_value = expected_client

        use_case = CreateClientUseCase(client_repository=mock_client_repository)

        # Act
        result = await use_case.execute(command)

        # Assert
        assert result.credit_limit == Decimal("0")
        assert result.available_credit == Decimal("0")

    async def test_create_client_owes_money_is_false_initially(self, mock_client_repository):
        """New client should not owe money initially."""
        pharmacy_id = uuid4()
        command = CreateClientDTO(
            pharmacy_id=pharmacy_id,
            phone="+54 9 11 1234 5678"
        )

        expected_client = Client(
            id=uuid4(),
            pharmacy_id=pharmacy_id,
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(Money.zero("ARS"), Money.zero("ARS"))
        )

        mock_client_repository.find_by_phone.return_value = None
        mock_client_repository.create.return_value = expected_client

        use_case = CreateClientUseCase(client_repository=mock_client_repository)

        # Act
        result = await use_case.execute(command)

        # Assert
        assert result.owes_money is False

    async def test_create_client_full_name_combination(self, mock_client_repository):
        """Should combine first and last name into full_name."""
        pharmacy_id = uuid4()
        command = CreateClientDTO(
            pharmacy_id=pharmacy_id,
            phone="+54 9 11 1234 5678",
            first_name="Juan",
            last_name="Pérez"
        )

        expected_client = Client(
            id=uuid4(),
            pharmacy_id=pharmacy_id,
            phone=Phone.create("+54 9 11 1234 5678"),
            first_name="Juan",
            last_name="Pérez",
            balance=ClientBalance.create(Money.zero("ARS"), Money.zero("ARS"))
        )

        mock_client_repository.find_by_phone.return_value = None
        mock_client_repository.create.return_value = expected_client

        use_case = CreateClientUseCase(client_repository=mock_client_repository)

        # Act
        result = await use_case.execute(command)

        # Assert
        assert result.full_name == "Juan Pérez"
