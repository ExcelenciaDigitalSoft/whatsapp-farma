"""Unit tests for Client entity."""
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest  # type: ignore

from app.domain.entities.client import Client
from app.domain.value_objects.phone import Phone
from app.domain.value_objects.money import Money
from app.domain.value_objects.client_balance import ClientBalance
from app.domain.value_objects.email import Email
from app.domain.exceptions import ValidationError, CreditLimitExceededError


class TestClientCreation:
    """Test client entity creation."""

    def test_create_client_with_required_fields(self):
        """Should create client with only required fields."""
        pharmacy_id = uuid4()
        phone = Phone.create("+54 9 11 1234 5678")
        balance = ClientBalance.create(
            Money.zero("ARS"),
            Money.create(Decimal("5000"), "ARS")
        )

        client = Client(
            pharmacy_id=pharmacy_id,
            phone=phone,
            balance=balance
        )

        assert client.pharmacy_id == pharmacy_id
        assert client.phone == phone
        assert client.balance == balance
        assert client.status == "active"
        assert client.id is not None

    def test_create_client_with_all_fields(self):
        """Should create client with all fields."""
        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            first_name="Juan",
            last_name="Pérez",
            email=Email.create("juan@example.com"),
            balance=ClientBalance.create(
                Money.zero("ARS"),
                Money.create(Decimal("5000"), "ARS")
            ),
            tags=["vip", "mayorista"],
            notes="Cliente importante"
        )

        assert client.first_name == "Juan"
        assert client.last_name == "Pérez"
        assert str(client.email) == "juan@example.com"
        assert "vip" in client.tags
        assert client.notes == "Cliente importante"

    def test_client_has_timestamps(self):
        """Should automatically set created_at and updated_at."""
        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(Money.zero("ARS"), Money.create(Decimal("5000"), "ARS"))
        )

        assert isinstance(client.created_at, datetime)
        assert isinstance(client.updated_at, datetime)


class TestClientFullName:
    """Test full_name property."""

    def test_full_name_with_both_names(self):
        """Should combine first and last name."""
        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            first_name="Juan",
            last_name="Pérez",
            balance=ClientBalance.create(Money.zero("ARS"), Money.create(Decimal("5000"), "ARS"))
        )

        assert client.full_name == "Juan Pérez"

    def test_full_name_with_only_first_name(self):
        """Should return first name only."""
        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            first_name="Juan",
            balance=ClientBalance.create(Money.zero("ARS"), Money.create(Decimal("5000"), "ARS"))
        )

        assert client.full_name == "Juan"

    def test_full_name_with_only_last_name(self):
        """Should return last name only."""
        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            last_name="Pérez",
            balance=ClientBalance.create(Money.zero("ARS"), Money.create(Decimal("5000"), "ARS"))
        )

        assert client.full_name == "Pérez"

    def test_full_name_with_no_names(self):
        """Should return None when no names."""
        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(Money.zero("ARS"), Money.create(Decimal("5000"), "ARS"))
        )

        assert client.full_name is None


class TestClientOwesMoneyProperty:
    """Test owes_money property delegation."""

    def test_owes_money_delegates_to_balance(self):
        """Should delegate to balance.owes_money."""
        balance_with_debt = ClientBalance(
            current_balance=Money(amount=Decimal("-1000"), currency="ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=balance_with_debt
        )

        assert client.owes_money is True


class TestCanMakePurchase:
    """Test purchase validation logic."""

    def test_can_make_purchase_when_active_and_within_limit(self):
        """Should allow purchase when active and within credit limit."""
        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(
                Money.zero("ARS"),
                Money.create(Decimal("5000"), "ARS")
            ),
            status="active"
        )

        assert client.can_make_purchase(Money.create(Decimal("3000"), "ARS"))

    def test_cannot_make_purchase_when_inactive(self):
        """Should not allow purchase when status is inactive."""
        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(
                Money.zero("ARS"),
                Money.create(Decimal("5000"), "ARS")
            ),
            status="inactive"
        )

        assert not client.can_make_purchase(Money.create(Decimal("1000"), "ARS"))

    def test_cannot_make_purchase_when_suspended(self):
        """Should not allow purchase when suspended."""
        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(
                Money.zero("ARS"),
                Money.create(Decimal("5000"), "ARS")
            ),
            status="suspended"
        )

        assert not client.can_make_purchase(Money.create(Decimal("1000"), "ARS"))

    def test_cannot_make_purchase_exceeding_credit(self):
        """Should not allow purchase exceeding available credit."""
        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(
                Money.zero("ARS"),
                Money.create(Decimal("5000"), "ARS")
            ),
            status="active"
        )

        assert not client.can_make_purchase(Money.create(Decimal("6000"), "ARS"))


class TestApplyCharge:
    """Test applying charges to client."""

    def test_apply_charge_updates_balance(self):
        """Should update client balance when charge applied."""
        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(
                Money.zero("ARS"),
                Money.create(Decimal("5000"), "ARS")
            ),
            status="active"
        )

        original_balance = client.balance
        client.apply_charge(Money.create(Decimal("1000"), "ARS"))

        assert client.balance != original_balance
        assert client.balance.current_balance.amount == Decimal("-1000")

    def test_apply_charge_raises_error_when_inactive(self):
        """Should raise error when trying to charge inactive client."""
        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(
                Money.zero("ARS"),
                Money.create(Decimal("5000"), "ARS")
            ),
            status="inactive"
        )

        with pytest.raises(ValidationError, match="Cannot charge inactive client"):
            client.apply_charge(Money.create(Decimal("1000"), "ARS"))

    def test_apply_charge_raises_error_exceeding_limit(self):
        """Should raise error when charge exceeds credit limit."""
        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(
                Money.zero("ARS"),
                Money.create(Decimal("5000"), "ARS")
            ),
            status="active"
        )

        with pytest.raises(CreditLimitExceededError):
            client.apply_charge(Money.create(Decimal("6000"), "ARS"))

    def test_apply_charge_updates_timestamp(self):
        """Should update updated_at timestamp."""
        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(
                Money.zero("ARS"),
                Money.create(Decimal("5000"), "ARS")
            ),
            status="active"
        )

        original_updated_at = client.updated_at
        client.apply_charge(Money.create(Decimal("1000"), "ARS"))

        assert client.updated_at > original_updated_at


class TestApplyPayment:
    """Test applying payments to client."""

    def test_apply_payment_reduces_debt(self):
        """Should reduce client debt when payment applied."""
        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance(
                current_balance=Money(amount=Decimal("-2000"), currency="ARS"),
                credit_limit=Money.create(Decimal("5000"), "ARS")
            ),
            status="active"
        )

        client.apply_payment(Money.create(Decimal("500"), "ARS"))

        assert client.balance.current_balance.amount == Decimal("-1500")

    def test_apply_payment_updates_timestamp(self):
        """Should update updated_at timestamp."""
        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance(
                current_balance=Money(amount=Decimal("-1000"), currency="ARS"),
                credit_limit=Money.create(Decimal("5000"), "ARS")
            ),
            status="active"
        )

        original_updated_at = client.updated_at
        client.apply_payment(Money.create(Decimal("500"), "ARS"))

        assert client.updated_at > original_updated_at


class TestClientActivation:
    """Test client activation/deactivation."""

    def test_activate_client(self):
        """Should set status to active."""
        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(Money.zero("ARS"), Money.create(Decimal("5000"), "ARS")),
            status="inactive"
        )

        client.activate()

        assert client.status == "active"

    def test_deactivate_client(self):
        """Should set status to inactive."""
        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(Money.zero("ARS"), Money.create(Decimal("5000"), "ARS")),
            status="active"
        )

        client.deactivate()

        assert client.status == "inactive"

    def test_suspend_client(self):
        """Should set status to suspended."""
        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(Money.zero("ARS"), Money.create(Decimal("5000"), "ARS")),
            status="active"
        )

        client.suspend()

        assert client.status == "suspended"


class TestClientMarkAsUpdated:
    """Test mark_as_updated method."""

    def test_mark_as_updated_changes_timestamp(self):
        """Should update the updated_at timestamp."""
        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(Money.zero("ARS"), Money.create(Decimal("5000"), "ARS"))
        )

        original_updated_at = client.updated_at
        client.mark_as_updated()

        assert client.updated_at > original_updated_at
