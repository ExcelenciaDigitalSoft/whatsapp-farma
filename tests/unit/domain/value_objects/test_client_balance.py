"""Unit tests for ClientBalance value object."""
from decimal import Decimal

import pytest  # type: ignore

from app.domain.value_objects.money import Money
from app.domain.value_objects.client_balance import ClientBalance
from app.domain.exceptions import ValidationError, CreditLimitExceededError


class TestClientBalanceCreation:
    """Test client balance creation."""

    def test_create_with_zero_balance_and_credit(self):
        """Should create balance with zero balance and credit limit."""
        balance = ClientBalance.create(
            current_balance=Money.zero("ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        assert balance.current_balance.is_zero()
        assert balance.credit_limit.amount == Decimal("5000")

    def test_create_with_positive_balance(self):
        """Should create balance with positive balance (customer has credit)."""
        balance = ClientBalance.create(
            current_balance=Money.create(Decimal("1000"), "ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        assert balance.current_balance.amount == Decimal("1000")

    def test_create_with_negative_balance(self):
        """Should create balance with negative balance (customer owes money)."""
        # Note: This uses Money.create_debt() which allows negative for debt tracking
        from app.domain.value_objects.money import Money

        balance = ClientBalance(
            current_balance=Money(amount=Decimal("-500"), currency="ARS"),  # Direct instantiation for debt
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        assert balance.current_balance.amount == Decimal("-500")
        assert balance.owes_money

    def test_create_with_different_currencies_raises_error(self):
        """Should raise error if currencies don't match."""
        with pytest.raises(ValidationError, match="Currency mismatch"):
            ClientBalance.create(
                current_balance=Money.create(Decimal("1000"), "ARS"),
                credit_limit=Money.create(Decimal("5000"), "USD")
            )

    def test_create_with_negative_credit_limit_raises_error(self):
        """Should raise error for negative credit limit."""
        with pytest.raises(ValidationError):
            ClientBalance.create(
                current_balance=Money.zero("ARS"),
                credit_limit=Money(amount=Decimal("-1000"), currency="ARS")
            )


class TestAvailableCredit:
    """Test available credit calculation."""

    def test_available_credit_with_zero_balance(self):
        """Full credit limit available with zero balance."""
        balance = ClientBalance.create(
            current_balance=Money.zero("ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        assert balance.available_credit.amount == Decimal("5000")

    def test_available_credit_with_positive_balance(self):
        """Credit limit + positive balance = total available."""
        balance = ClientBalance.create(
            current_balance=Money.create(Decimal("1000"), "ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        # Customer has 1000 in their favor + 5000 credit = 6000 available
        assert balance.available_credit.amount == Decimal("6000")

    def test_available_credit_with_debt(self):
        """Credit limit - debt = remaining available."""
        balance = ClientBalance(
            current_balance=Money(amount=Decimal("-2000"), currency="ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        # 5000 credit - 2000 debt = 3000 available
        assert balance.available_credit.amount == Decimal("3000")

    def test_available_credit_when_debt_exceeds_limit(self):
        """Available credit is zero when debt exceeds limit."""
        balance = ClientBalance(
            current_balance=Money(amount=Decimal("-6000"), currency="ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        # Over limit, no available credit
        assert balance.available_credit.amount == Decimal("0")


class TestCanPurchase:
    """Test purchase validation logic."""

    def test_can_purchase_within_credit_limit(self):
        """Should allow purchase within available credit."""
        balance = ClientBalance.create(
            current_balance=Money.zero("ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        assert balance.can_purchase(Money.create(Decimal("3000"), "ARS"))

    def test_can_purchase_exactly_at_credit_limit(self):
        """Should allow purchase exactly at credit limit."""
        balance = ClientBalance.create(
            current_balance=Money.zero("ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        assert balance.can_purchase(Money.create(Decimal("5000"), "ARS"))

    def test_cannot_purchase_exceeding_credit_limit(self):
        """Should not allow purchase exceeding credit limit."""
        balance = ClientBalance.create(
            current_balance=Money.zero("ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        assert not balance.can_purchase(Money.create(Decimal("5001"), "ARS"))

    def test_can_purchase_with_existing_positive_balance(self):
        """Should allow larger purchase with positive balance."""
        balance = ClientBalance.create(
            current_balance=Money.create(Decimal("2000"), "ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        # 2000 + 5000 = 7000 available
        assert balance.can_purchase(Money.create(Decimal("7000"), "ARS"))

    def test_can_purchase_with_existing_debt(self):
        """Should reduce available credit by existing debt."""
        balance = ClientBalance(
            current_balance=Money(amount=Decimal("-1000"), currency="ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        # 5000 - 1000 debt = 4000 available
        assert balance.can_purchase(Money.create(Decimal("4000"), "ARS"))
        assert not balance.can_purchase(Money.create(Decimal("4001"), "ARS"))


class TestApplyCharge:
    """Test applying charges to balance."""

    def test_apply_charge_creates_debt(self):
        """Applying charge should decrease balance (create debt)."""
        balance = ClientBalance.create(
            current_balance=Money.zero("ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        new_balance = balance.apply_charge(Money.create(Decimal("1000"), "ARS"))

        assert new_balance.current_balance.amount == Decimal("-1000")
        assert new_balance.owes_money

    def test_apply_charge_to_positive_balance(self):
        """Charge reduces positive balance first."""
        balance = ClientBalance.create(
            current_balance=Money.create(Decimal("2000"), "ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        new_balance = balance.apply_charge(Money.create(Decimal("500"), "ARS"))

        assert new_balance.current_balance.amount == Decimal("1500")
        assert not new_balance.owes_money

    def test_apply_charge_exceeding_credit_limit_raises_error(self):
        """Should raise error when charge exceeds available credit."""
        balance = ClientBalance.create(
            current_balance=Money.zero("ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        with pytest.raises(CreditLimitExceededError):
            balance.apply_charge(Money.create(Decimal("6000"), "ARS"))

    def test_apply_charge_is_immutable(self):
        """Should return new instance, not modify original."""
        original = ClientBalance.create(
            current_balance=Money.zero("ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        new_balance = original.apply_charge(Money.create(Decimal("1000"), "ARS"))

        assert original.current_balance.is_zero()  # Unchanged
        assert new_balance.current_balance.amount == Decimal("-1000")


class TestApplyPayment:
    """Test applying payments to balance."""

    def test_apply_payment_reduces_debt(self):
        """Payment should reduce debt."""
        balance = ClientBalance(
            current_balance=Money(amount=Decimal("-2000"), currency="ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        new_balance = balance.apply_payment(Money.create(Decimal("500"), "ARS"))

        assert new_balance.current_balance.amount == Decimal("-1500")

    def test_apply_payment_clears_debt(self):
        """Payment should fully clear debt."""
        balance = ClientBalance(
            current_balance=Money(amount=Decimal("-1000"), currency="ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        new_balance = balance.apply_payment(Money.create(Decimal("1000"), "ARS"))

        assert new_balance.current_balance.is_zero()
        assert not new_balance.owes_money

    def test_apply_payment_creates_positive_balance(self):
        """Overpayment creates positive balance (customer credit)."""
        balance = ClientBalance(
            current_balance=Money(amount=Decimal("-500"), currency="ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        new_balance = balance.apply_payment(Money.create(Decimal("1000"), "ARS"))

        assert new_balance.current_balance.amount == Decimal("500")
        assert not new_balance.owes_money

    def test_apply_payment_is_immutable(self):
        """Should return new instance, not modify original."""
        original = ClientBalance(
            current_balance=Money(amount=Decimal("-1000"), currency="ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        new_balance = original.apply_payment(Money.create(Decimal("500"), "ARS"))

        assert original.current_balance.amount == Decimal("-1000")  # Unchanged
        assert new_balance.current_balance.amount == Decimal("-500")


class TestOwesMoneyProperty:
    """Test owes_money property."""

    def test_owes_money_true_with_negative_balance(self):
        """Should return True when balance is negative."""
        balance = ClientBalance(
            current_balance=Money(amount=Decimal("-100"), currency="ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        assert balance.owes_money

    def test_owes_money_false_with_zero_balance(self):
        """Should return False with zero balance."""
        balance = ClientBalance.create(
            current_balance=Money.zero("ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        assert not balance.owes_money

    def test_owes_money_false_with_positive_balance(self):
        """Should return False with positive balance."""
        balance = ClientBalance.create(
            current_balance=Money.create(Decimal("1000"), "ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        assert not balance.owes_money


class TestClientBalanceImmutability:
    """Test immutability of ClientBalance."""

    def test_balance_is_frozen(self):
        """Should not allow modification after creation."""
        balance = ClientBalance.create(
            current_balance=Money.zero("ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        with pytest.raises(Exception):
            balance.current_balance = Money.create(Decimal("1000"), "ARS")  # type: ignore

    def test_operations_return_new_instances(self):
        """All operations should return new instances."""
        original = ClientBalance.create(
            current_balance=Money.zero("ARS"),
            credit_limit=Money.create(Decimal("5000"), "ARS")
        )

        charged = original.apply_charge(Money.create(Decimal("1000"), "ARS"))

        assert charged is not original
        assert original.current_balance.is_zero()
