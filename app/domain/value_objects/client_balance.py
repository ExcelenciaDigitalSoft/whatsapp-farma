"""Client balance value object."""
from dataclasses import dataclass
from .money import Money


@dataclass(frozen=True)
class ClientBalance:
    """
    Client balance value object.

    Encapsulates client financial state including credit limit and current balance.
    Negative balance means client owes money to the pharmacy.

    Attributes:
        current_balance: Current account balance (Money)
        credit_limit: Maximum credit allowed (Money)
    """

    current_balance: Money
    credit_limit: Money

    def __post_init__(self):
        """Validate balance after initialization."""
        if self.current_balance.currency != self.credit_limit.currency:
            raise ValueError(
                f"Currency mismatch: balance={self.current_balance.currency}, "
                f"limit={self.credit_limit.currency}"
            )

        # Ensure credit limit is non-negative
        if self.credit_limit.is_negative():
            raise ValueError("Credit limit cannot be negative")

    @classmethod
    def create(
        cls,
        current_balance: Money,
        credit_limit: Money | None = None,
    ) -> "ClientBalance":
        """
        Create a ClientBalance value object.

        Args:
            current_balance: Current balance
            credit_limit: Credit limit (defaults to zero)

        Returns:
            ClientBalance value object
        """
        if credit_limit is None:
            credit_limit = Money.zero(current_balance.currency)

        return cls(current_balance=current_balance, credit_limit=credit_limit)

    @classmethod
    def zero(cls, currency: str = "ARS") -> "ClientBalance":
        """Create a zero balance."""
        return cls(
            current_balance=Money.zero(currency),
            credit_limit=Money.zero(currency),
        )

    @property
    def available_credit(self) -> Money:
        """
        Calculate available credit.

        Returns:
            Available credit amount (credit_limit + current_balance if negative)
        """
        if self.current_balance.is_negative():
            # Client owes money, available credit is reduced
            return self.credit_limit + self.current_balance  # current_balance is negative
        else:
            # Client has positive balance, full credit limit available
            return self.credit_limit

    @property
    def total_debt(self) -> Money:
        """
        Get total debt amount.

        Returns:
            Absolute value of negative balance, or zero if balance is positive
        """
        if self.current_balance.is_negative():
            return self.current_balance.abs()
        return Money.zero(self.current_balance.currency)

    @property
    def is_in_debt(self) -> bool:
        """Check if client owes money."""
        return self.current_balance.is_negative()

    @property
    def owes_money(self) -> bool:
        """Check if client owes money (alias for is_in_debt)."""
        return self.is_in_debt

    @property
    def is_credit_exceeded(self) -> bool:
        """Check if client has exceeded credit limit."""
        if not self.current_balance.is_negative():
            return False

        debt = self.current_balance.abs()
        return debt > self.credit_limit

    @property
    def is_at_credit_limit(self) -> bool:
        """Check if client is at or near credit limit (within 10%)."""
        if not self.current_balance.is_negative():
            return False

        debt = self.current_balance.abs()
        threshold = self.credit_limit * 0.9  # 90% of credit limit
        return debt >= threshold

    def can_purchase(self, amount: Money) -> bool:
        """
        Check if client can make a purchase of given amount.

        Args:
            amount: Purchase amount

        Returns:
            True if purchase is allowed, False otherwise
        """
        if amount.currency != self.current_balance.currency:
            raise ValueError(f"Currency mismatch: {amount.currency} != {self.current_balance.currency}")

        # Calculate balance after purchase
        projected_balance = self.current_balance - amount

        # If projected balance is positive or within credit limit
        if projected_balance.is_positive() or projected_balance.is_zero():
            return True

        # Check if debt would exceed credit limit
        projected_debt = projected_balance.abs()
        return projected_debt <= self.credit_limit

    def apply_charge(self, amount: Money) -> "ClientBalance":
        """
        Apply a charge to the balance.

        Args:
            amount: Amount to charge

        Returns:
            New ClientBalance with updated balance
        """
        new_balance = self.current_balance - amount
        return ClientBalance(current_balance=new_balance, credit_limit=self.credit_limit)

    def apply_payment(self, amount: Money) -> "ClientBalance":
        """
        Apply a payment to the balance.

        Args:
            amount: Payment amount

        Returns:
            New ClientBalance with updated balance
        """
        new_balance = self.current_balance + amount
        return ClientBalance(current_balance=new_balance, credit_limit=self.credit_limit)

    def update_credit_limit(self, new_limit: Money) -> "ClientBalance":
        """
        Update credit limit.

        Args:
            new_limit: New credit limit

        Returns:
            New ClientBalance with updated limit
        """
        return ClientBalance(current_balance=self.current_balance, credit_limit=new_limit)

    def __str__(self) -> str:
        """String representation."""
        status = "IN DEBT" if self.is_in_debt else "CREDIT"
        return f"Balance: {self.current_balance} ({status}), Credit Limit: {self.credit_limit}"

    def __repr__(self) -> str:
        """Repr representation."""
        return (
            f"ClientBalance(current_balance={self.current_balance!r}, "
            f"credit_limit={self.credit_limit!r})"
        )
