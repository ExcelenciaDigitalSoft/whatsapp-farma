"""Money value object for currency handling."""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass(frozen=True)
class Money:
    """
    Money value object representing monetary amounts with currency.

    Immutable value object that ensures:
    - Type safety for monetary operations
    - Currency consistency
    - Proper decimal precision for financial calculations

    Attributes:
        amount: The monetary amount as Decimal
        currency: The currency code (ISO 4217)
    """

    amount: Decimal
    currency: str = "ARS"

    def __post_init__(self):
        """Validate money object after initialization."""
        # Convert to Decimal if needed
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, "amount", Decimal(str(self.amount)))

        # Validate currency code
        if len(self.currency) != 3:
            raise ValueError(f"Invalid currency code: {self.currency}")

        # Round to 2 decimal places
        rounded = self.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        object.__setattr__(self, "amount", rounded)

    @classmethod
    def create(cls, amount: int | float | str | Decimal, currency: str = "ARS") -> "Money":
        """
        Create a Money value object.

        Args:
            amount: The monetary amount
            currency: The currency code (default: ARS)

        Returns:
            Money value object
        """
        return cls(amount=Decimal(str(amount)), currency=currency.upper())

    @classmethod
    def zero(cls, currency: str = "ARS") -> "Money":
        """Create a zero money value."""
        return cls(amount=Decimal("0"), currency=currency)

    def add(self, other: "Money") -> "Money":
        """
        Add two money values.

        Args:
            other: Money to add

        Returns:
            New Money with sum

        Raises:
            ValueError: If currencies don't match
        """
        if self.currency != other.currency:
            raise ValueError(f"Cannot add different currencies: {self.currency} and {other.currency}")

        return Money(amount=self.amount + other.amount, currency=self.currency)

    def subtract(self, other: "Money") -> "Money":
        """
        Subtract money values.

        Args:
            other: Money to subtract

        Returns:
            New Money with difference

        Raises:
            ValueError: If currencies don't match
        """
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot subtract different currencies: {self.currency} and {other.currency}"
            )

        return Money(amount=self.amount - other.amount, currency=self.currency)

    def multiply(self, multiplier: int | float | Decimal) -> "Money":
        """
        Multiply money by a scalar.

        Args:
            multiplier: The multiplication factor

        Returns:
            New Money with product
        """
        result = self.amount * Decimal(str(multiplier))
        return Money(amount=result, currency=self.currency)

    def divide(self, divisor: int | float | Decimal) -> "Money":
        """
        Divide money by a scalar.

        Args:
            divisor: The division factor

        Returns:
            New Money with quotient

        Raises:
            ValueError: If divisor is zero
        """
        if divisor == 0:
            raise ValueError("Cannot divide by zero")

        result = self.amount / Decimal(str(divisor))
        return Money(amount=result, currency=self.currency)

    def negate(self) -> "Money":
        """Get the negative of this money value."""
        return Money(amount=-self.amount, currency=self.currency)

    def is_positive(self) -> bool:
        """Check if amount is positive."""
        return self.amount > 0

    def is_negative(self) -> bool:
        """Check if amount is negative."""
        return self.amount < 0

    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self.amount == 0

    def is_greater_than(self, other: "Money") -> bool:
        """
        Check if this money is greater than another.

        Args:
            other: Money to compare with

        Returns:
            True if this money is greater than other

        Raises:
            ValueError: If currencies don't match
        """
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare different currencies: {self.currency} and {other.currency}")
        return self.amount > other.amount

    def is_less_than(self, other: "Money") -> bool:
        """
        Check if this money is less than another.

        Args:
            other: Money to compare with

        Returns:
            True if this money is less than other

        Raises:
            ValueError: If currencies don't match
        """
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare different currencies: {self.currency} and {other.currency}")
        return self.amount < other.amount

    def abs(self) -> "Money":
        """Get absolute value."""
        return Money(amount=abs(self.amount), currency=self.currency)

    def __add__(self, other: "Money") -> "Money":
        """Operator overload for addition."""
        return self.add(other)

    def __sub__(self, other: "Money") -> "Money":
        """Operator overload for subtraction."""
        return self.subtract(other)

    def __mul__(self, multiplier: int | float | Decimal) -> "Money":
        """Operator overload for multiplication."""
        return self.multiply(multiplier)

    def __truediv__(self, divisor: int | float | Decimal) -> "Money":
        """Operator overload for division."""
        return self.divide(divisor)

    def __neg__(self) -> "Money":
        """Operator overload for negation."""
        return self.negate()

    def __abs__(self) -> "Money":
        """Operator overload for absolute value."""
        return self.abs()

    def __eq__(self, other: object) -> bool:
        """Compare money values."""
        if not isinstance(other, Money):
            return False
        return self.amount == other.amount and self.currency == other.currency

    def __lt__(self, other: "Money") -> bool:
        """Less than comparison."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare different currencies: {self.currency} and {other.currency}")
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        """Less than or equal comparison."""
        return self == other or self < other

    def __gt__(self, other: "Money") -> bool:
        """Greater than comparison."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare different currencies: {self.currency} and {other.currency}")
        return self.amount > other.amount

    def __ge__(self, other: "Money") -> bool:
        """Greater than or equal comparison."""
        return self == other or self > other

    def __str__(self) -> str:
        """String representation."""
        return f"{self.currency} {self.amount:.2f}"

    def __repr__(self) -> str:
        """Repr representation."""
        return f"Money(amount={self.amount}, currency='{self.currency}')"

    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash((self.amount, self.currency))

    def formatted(self, symbol: bool = True) -> str:
        """
        Get formatted string representation.

        Args:
            symbol: Include currency symbol (default: True)

        Returns:
            Formatted money string
        """
        symbols = {
            "ARS": "$",
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
        }

        amount_str = f"{self.amount:,.2f}"

        if symbol and self.currency in symbols:
            return f"{symbols[self.currency]} {amount_str}"
        return f"{self.currency} {amount_str}"
