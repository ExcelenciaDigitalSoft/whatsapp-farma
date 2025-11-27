"""Unit tests for ClientValidator domain service."""
from decimal import Decimal
from uuid import uuid4

import pytest  # type: ignore

from app.domain.services.client_validator import ClientValidator
from app.domain.entities.client import Client
from app.domain.value_objects.phone import Phone
from app.domain.value_objects.money import Money
from app.domain.value_objects.client_balance import ClientBalance
from app.domain.exceptions import ValidationError, CreditLimitExceededError


class TestValidateForTransaction:
    """Test client validation for transactions."""

    def test_validate_active_client_within_limit(self):
        """Should pass validation for active client within credit limit."""
        validator = ClientValidator()

        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(
                Money.zero("ARS"),
                Money.create(Decimal("5000"), "ARS")
            ),
            status="active"
        )

        # Should not raise any exception
        validator.validate_for_transaction(client, Money.create(Decimal("3000"), "ARS"))

    def test_validate_inactive_client_raises_error(self):
        """Should raise error for inactive client."""
        validator = ClientValidator()

        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(
                Money.zero("ARS"),
                Money.create(Decimal("5000"), "ARS")
            ),
            status="inactive"
        )

        with pytest.raises(ValidationError, match="Client is not active"):
            validator.validate_for_transaction(client, Money.create(Decimal("1000"), "ARS"))

    def test_validate_suspended_client_raises_error(self):
        """Should raise error for suspended client."""
        validator = ClientValidator()

        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(
                Money.zero("ARS"),
                Money.create(Decimal("5000"), "ARS")
            ),
            status="suspended"
        )

        with pytest.raises(ValidationError, match="Client is not active"):
            validator.validate_for_transaction(client, Money.create(Decimal("1000"), "ARS"))

    def test_validate_exceeding_credit_limit_raises_error(self):
        """Should raise error when amount exceeds credit limit."""
        validator = ClientValidator()

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
            validator.validate_for_transaction(client, Money.create(Decimal("6000"), "ARS"))

    def test_validate_exactly_at_limit_passes(self):
        """Should pass when amount exactly equals credit limit."""
        validator = ClientValidator()

        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(
                Money.zero("ARS"),
                Money.create(Decimal("5000"), "ARS")
            ),
            status="active"
        )

        # Should not raise
        validator.validate_for_transaction(client, Money.create(Decimal("5000"), "ARS"))

    def test_validate_with_existing_debt(self):
        """Should consider existing debt when validating."""
        validator = ClientValidator()

        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance(
                current_balance=Money(amount=Decimal("-2000"), currency="ARS"),
                credit_limit=Money.create(Decimal("5000"), "ARS")
            ),
            status="active"
        )

        # 5000 limit - 2000 debt = 3000 available
        # Should pass with 3000
        validator.validate_for_transaction(client, Money.create(Decimal("3000"), "ARS"))

        # Should fail with 3001
        with pytest.raises(CreditLimitExceededError):
            validator.validate_for_transaction(client, Money.create(Decimal("3001"), "ARS"))


class TestValidateClientData:
    """Test client data validation."""

    def test_validate_valid_phone_format(self):
        """Should validate correct phone format."""
        validator = ClientValidator()

        # Should not raise
        validator.validate_phone("+54 9 11 1234 5678")

    def test_validate_invalid_phone_raises_error(self):
        """Should raise error for invalid phone."""
        validator = ClientValidator()

        with pytest.raises(ValidationError):
            validator.validate_phone("invalid")

    def test_validate_valid_email_format(self):
        """Should validate correct email format."""
        validator = ClientValidator()

        # Should not raise
        validator.validate_email("test@example.com")

    def test_validate_invalid_email_raises_error(self):
        """Should raise error for invalid email."""
        validator = ClientValidator()

        with pytest.raises(ValidationError, match="Invalid email format"):
            validator.validate_email("invalid-email")

    def test_validate_email_with_special_characters(self):
        """Should accept valid emails with special characters."""
        validator = ClientValidator()

        # Should not raise
        validator.validate_email("user+tag@example.co.uk")
        validator.validate_email("first.last@example.com")

    def test_validate_credit_limit_positive(self):
        """Should validate positive credit limit."""
        validator = ClientValidator()

        # Should not raise
        validator.validate_credit_limit(Decimal("5000"))

    def test_validate_credit_limit_zero(self):
        """Should accept zero credit limit."""
        validator = ClientValidator()

        # Should not raise
        validator.validate_credit_limit(Decimal("0"))

    def test_validate_credit_limit_negative_raises_error(self):
        """Should raise error for negative credit limit."""
        validator = ClientValidator()

        with pytest.raises(ValidationError, match="Credit limit cannot be negative"):
            validator.validate_credit_limit(Decimal("-100"))


class TestValidateClientStatus:
    """Test client status validation."""

    def test_validate_valid_status_active(self):
        """Should accept 'active' status."""
        validator = ClientValidator()

        validator.validate_status("active")

    def test_validate_valid_status_inactive(self):
        """Should accept 'inactive' status."""
        validator = ClientValidator()

        validator.validate_status("inactive")

    def test_validate_valid_status_suspended(self):
        """Should accept 'suspended' status."""
        validator = ClientValidator()

        validator.validate_status("suspended")

    def test_validate_invalid_status_raises_error(self):
        """Should raise error for invalid status."""
        validator = ClientValidator()

        with pytest.raises(ValidationError, match="Invalid client status"):
            validator.validate_status("invalid_status")


class TestEdgeCases:
    """Test edge cases for client validation."""

    def test_validate_very_large_amount_within_limit(self):
        """Should handle very large amounts."""
        validator = ClientValidator()

        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(
                Money.zero("ARS"),
                Money.create(Decimal("1000000"), "ARS")
            ),
            status="active"
        )

        validator.validate_for_transaction(client, Money.create(Decimal("999999"), "ARS"))

    def test_validate_very_small_amount(self):
        """Should handle very small amounts."""
        validator = ClientValidator()

        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(
                Money.zero("ARS"),
                Money.create(Decimal("5000"), "ARS")
            ),
            status="active"
        )

        validator.validate_for_transaction(client, Money.create(Decimal("0.01"), "ARS"))

    def test_validate_with_positive_balance_increases_available(self):
        """Client with positive balance has more available credit."""
        validator = ClientValidator()

        client = Client(
            pharmacy_id=uuid4(),
            phone=Phone.create("+54 9 11 1234 5678"),
            balance=ClientBalance.create(
                Money.create(Decimal("2000"), "ARS"),  # Positive balance
                Money.create(Decimal("5000"), "ARS")
            ),
            status="active"
        )

        # 2000 + 5000 = 7000 available
        validator.validate_for_transaction(client, Money.create(Decimal("7000"), "ARS"))
