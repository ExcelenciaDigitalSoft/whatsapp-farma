"""Unit tests for Money value object."""
from decimal import Decimal

import pytest  # type: ignore

from app.domain.value_objects.money import Money
from app.domain.exceptions import ValidationError


class TestMoneyCreation:
    """Test money creation and validation."""

    def test_create_with_decimal(self):
        """Should create money with Decimal amount."""
        money = Money.create(Decimal("100.50"), "ARS")

        assert money.amount == Decimal("100.50")
        assert money.currency == "ARS"

    def test_create_with_int(self):
        """Should create money from integer."""
        money = Money.create(100, "USD")

        assert money.amount == Decimal("100")
        assert money.currency == "USD"

    def test_create_with_float(self):
        """Should create money from float."""
        money = Money.create(100.50, "EUR")

        assert money.amount == Decimal("100.50")

    def test_create_with_string(self):
        """Should create money from string."""
        money = Money.create("100.50", "GBP")

        assert money.amount == Decimal("100.50")

    def test_create_with_negative_amount_raises_error(self):
        """Should raise error for negative amounts."""
        with pytest.raises(ValidationError, match="Amount cannot be negative"):
            Money.create(Decimal("-100"), "ARS")

    def test_create_zero_money(self):
        """Should create zero money value."""
        money = Money.zero("ARS")

        assert money.amount == Decimal("0")
        assert money.currency == "ARS"
        assert money.is_zero()

    def test_create_with_invalid_currency_raises_error(self):
        """Should validate currency code."""
        with pytest.raises(ValidationError, match="Invalid currency"):
            Money.create(Decimal("100"), "INVALID")

    def test_create_with_too_many_decimal_places(self):
        """Should round to 2 decimal places."""
        money = Money.create(Decimal("100.999"), "ARS")

        assert money.amount == Decimal("101.00")


class TestMoneyArithmetic:
    """Test money arithmetic operations."""

    def test_add_same_currency(self):
        """Should add money with same currency."""
        money1 = Money.create(Decimal("100"), "ARS")
        money2 = Money.create(Decimal("50"), "ARS")

        result = money1.add(money2)

        assert result.amount == Decimal("150")
        assert result.currency == "ARS"

    def test_add_different_currency_raises_error(self):
        """Should raise error when adding different currencies."""
        money1 = Money.create(Decimal("100"), "ARS")
        money2 = Money.create(Decimal("50"), "USD")

        with pytest.raises(ValueError, match="Cannot add different currencies"):
            money1.add(money2)

    def test_subtract_same_currency(self):
        """Should subtract money with same currency."""
        money1 = Money.create(Decimal("100"), "ARS")
        money2 = Money.create(Decimal("30"), "ARS")

        result = money1.subtract(money2)

        assert result.amount == Decimal("70")
        assert result.currency == "ARS"

    def test_subtract_different_currency_raises_error(self):
        """Should raise error when subtracting different currencies."""
        money1 = Money.create(Decimal("100"), "ARS")
        money2 = Money.create(Decimal("50"), "USD")

        with pytest.raises(ValueError, match="Cannot subtract different currencies"):
            money1.subtract(money2)

    def test_subtract_resulting_in_negative_raises_error(self):
        """Should raise error when subtraction results in negative."""
        money1 = Money.create(Decimal("50"), "ARS")
        money2 = Money.create(Decimal("100"), "ARS")

        with pytest.raises(ValidationError, match="Result cannot be negative"):
            money1.subtract(money2)

    def test_multiply_by_integer(self):
        """Should multiply money by integer."""
        money = Money.create(Decimal("100"), "ARS")

        result = money.multiply(3)

        assert result.amount == Decimal("300")
        assert result.currency == "ARS"

    def test_multiply_by_decimal(self):
        """Should multiply money by decimal."""
        money = Money.create(Decimal("100"), "ARS")

        result = money.multiply(Decimal("1.5"))

        assert result.amount == Decimal("150.00")

    def test_multiply_by_negative_raises_error(self):
        """Should raise error when multiplying by negative."""
        money = Money.create(Decimal("100"), "ARS")

        with pytest.raises(ValidationError, match="Multiplier cannot be negative"):
            money.multiply(-2)

    def test_divide_by_integer(self):
        """Should divide money by integer."""
        money = Money.create(Decimal("100"), "ARS")

        result = money.divide(4)

        assert result.amount == Decimal("25.00")

    def test_divide_by_zero_raises_error(self):
        """Should raise error when dividing by zero."""
        money = Money.create(Decimal("100"), "ARS")

        with pytest.raises(ZeroDivisionError):
            money.divide(0)


class TestMoneyComparison:
    """Test money comparison operations."""

    def test_is_greater_than_same_currency(self):
        """Should compare amounts with same currency."""
        money1 = Money.create(Decimal("100"), "ARS")
        money2 = Money.create(Decimal("50"), "ARS")

        assert money1.is_greater_than(money2)
        assert not money2.is_greater_than(money1)

    def test_is_greater_than_different_currency_raises_error(self):
        """Should raise error comparing different currencies."""
        money1 = Money.create(Decimal("100"), "ARS")
        money2 = Money.create(Decimal("50"), "USD")

        with pytest.raises(ValueError, match="Cannot compare different currencies"):
            money1.is_greater_than(money2)

    def test_is_less_than_same_currency(self):
        """Should compare amounts with same currency."""
        money1 = Money.create(Decimal("50"), "ARS")
        money2 = Money.create(Decimal("100"), "ARS")

        assert money1.is_less_than(money2)
        assert not money2.is_less_than(money1)

    def test_is_zero(self):
        """Should identify zero amounts."""
        zero = Money.zero("ARS")
        non_zero = Money.create(Decimal("0.01"), "ARS")

        assert zero.is_zero()
        assert not non_zero.is_zero()

    def test_is_positive(self):
        """Should identify positive amounts."""
        positive = Money.create(Decimal("100"), "ARS")
        zero = Money.zero("ARS")

        assert positive.is_positive()
        assert not zero.is_positive()

    def test_is_negative(self):
        """Money cannot be negative, so always False."""
        money = Money.create(Decimal("100"), "ARS")
        zero = Money.zero("ARS")

        assert not money.is_negative()
        assert not zero.is_negative()


class TestMoneyEquality:
    """Test money equality."""

    def test_equal_same_amount_and_currency(self):
        """Should be equal with same amount and currency."""
        money1 = Money.create(Decimal("100.00"), "ARS")
        money2 = Money.create(Decimal("100.00"), "ARS")

        assert money1 == money2

    def test_not_equal_different_amount(self):
        """Should not be equal with different amounts."""
        money1 = Money.create(Decimal("100"), "ARS")
        money2 = Money.create(Decimal("50"), "ARS")

        assert money1 != money2

    def test_not_equal_different_currency(self):
        """Should not be equal with different currencies."""
        money1 = Money.create(Decimal("100"), "ARS")
        money2 = Money.create(Decimal("100"), "USD")

        assert money1 != money2


class TestMoneyImmutability:
    """Test money immutability."""

    def test_money_is_frozen(self):
        """Should not allow modification after creation."""
        money = Money.create(Decimal("100"), "ARS")

        with pytest.raises(Exception):
            money.amount = Decimal("200")  # type: ignore

    def test_arithmetic_returns_new_instance(self):
        """Arithmetic operations should return new instances."""
        original = Money.create(Decimal("100"), "ARS")
        result = original.add(Money.create(Decimal("50"), "ARS"))

        assert result is not original
        assert original.amount == Decimal("100")  # Unchanged


class TestMoneyStringRepresentation:
    """Test string representation."""

    def test_str_format(self):
        """Should format as currency string."""
        money = Money.create(Decimal("1234.56"), "ARS")

        assert str(money) == "ARS 1234.56"

    def test_repr_format(self):
        """Should show class and values in repr."""
        money = Money.create(Decimal("100"), "USD")
        repr_str = repr(money)

        assert "Money" in repr_str
        assert "100" in repr_str
        assert "USD" in repr_str


class TestMoneyEdgeCases:
    """Test edge cases."""

    def test_very_large_amounts(self):
        """Should handle very large amounts."""
        money = Money.create(Decimal("999999999999.99"), "ARS")

        assert money.amount == Decimal("999999999999.99")

    def test_very_small_non_zero_amounts(self):
        """Should handle amounts like 0.01."""
        money = Money.create(Decimal("0.01"), "ARS")

        assert money.amount == Decimal("0.01")
        assert not money.is_zero()

    def test_abs_always_returns_positive(self):
        """abs() should return the money as-is (already positive)."""
        money = Money.create(Decimal("100"), "ARS")

        result = money.abs()

        assert result == money
        assert result.amount == Decimal("100")
