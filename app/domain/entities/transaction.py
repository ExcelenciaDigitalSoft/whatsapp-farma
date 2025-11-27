"""Transaction domain entity."""
from dataclasses import dataclass, field
from datetime import datetime, date
from uuid import UUID
from typing import Any

from .base import BaseEntity
from app.domain.value_objects import Money
from app.domain.exceptions import ValidationError, InvalidStateTransitionError


@dataclass
class TransactionItem:
    """
    Transaction line item.

    Represents a single item in a transaction.
    """

    name: str
    quantity: int
    unit_price: Money
    total: Money

    def __post_init__(self):
        """Validate item."""
        if self.quantity <= 0:
            raise ValidationError("Quantity must be positive")

        if self.unit_price.is_negative():
            raise ValidationError("Unit price cannot be negative")

        # Validate total matches quantity * unit_price
        expected_total = self.unit_price * self.quantity
        if abs((self.total - expected_total).amount) > 0.01:  # Allow for rounding
            raise ValidationError(
                f"Total {self.total} doesn't match quantity * unit_price = {expected_total}"
            )


@dataclass(kw_only=True)
class Transaction(BaseEntity):
    """
    Transaction domain entity for all financial operations.

    Supports:
    - Invoices, payments, credit notes, debit notes
    - Payment gateway integration
    - Invoice generation
    - Multi-currency support

    Attributes:
        pharmacy_id: Pharmacy that owns this transaction
        client_id: Client associated with this transaction
        transaction_number: Unique transaction number
        transaction_type: Type (invoice, payment, credit_note, debit_note)
        amount: Base amount before tax/discount
        currency: Currency code
        tax_amount: Tax amount
        discount_amount: Discount amount
        total_amount: Final total amount
        payment_method: Payment method used
        payment_status: Payment status
        description: Transaction description
        items: Line items
        transaction_date: Transaction date
        due_date: Payment due date
        paid_at: Payment timestamp
    """

    pharmacy_id: UUID
    client_id: UUID
    transaction_number: str
    transaction_type: str
    total_amount: Money
    payment_status: str = "pending"

    # Amounts
    amount: Money | None = None
    tax_amount: Money = field(default_factory=lambda: Money.zero())
    discount_amount: Money = field(default_factory=lambda: Money.zero())

    # Payment details
    payment_method: str | None = None

    # Payment gateway integration
    mercadopago_payment_id: str | None = None
    mercadopago_payment_link: str | None = None
    mercadopago_preference_id: str | None = None

    # Description & items
    description: str | None = None
    items: list[TransactionItem] = field(default_factory=list)

    # Invoice details
    invoice_pdf_path: str | None = None
    invoice_sent_at: datetime | None = None

    # Dates
    transaction_date: date = field(default_factory=date.today)
    due_date: date | None = None
    paid_at: datetime | None = None

    # Cancellation
    cancelled_at: datetime | None = None
    cancelled_by: UUID | None = None

    # Metadata
    extra_metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate transaction after initialization."""
        self.validate()

    def validate(self) -> None:
        """
        Validate transaction business rules.

        Raises:
            ValidationError: If validation fails
        """
        valid_types = ["invoice", "payment", "credit_note", "debit_note"]
        if self.transaction_type not in valid_types:
            raise ValidationError(f"Invalid transaction type: {self.transaction_type}")

        valid_statuses = ["pending", "completed", "failed", "cancelled", "refunded"]
        if self.payment_status not in valid_statuses:
            raise ValidationError(f"Invalid payment status: {self.payment_status}")

        if self.total_amount.is_negative() and self.transaction_type in ["invoice", "debit_note"]:
            raise ValidationError(f"{self.transaction_type} cannot have negative amount")

        # Validate currency consistency
        if self.amount and self.amount.currency != self.total_amount.currency:
            raise ValidationError("Currency mismatch in transaction amounts")

    @property
    def is_paid(self) -> bool:
        """Check if transaction is paid."""
        return self.payment_status == "completed"

    @property
    def is_pending(self) -> bool:
        """Check if transaction is pending payment."""
        return self.payment_status == "pending"

    @property
    def is_cancelled(self) -> bool:
        """Check if transaction is cancelled."""
        return self.payment_status == "cancelled"

    @property
    def is_overdue(self) -> bool:
        """Check if transaction is overdue."""
        if self.due_date is None or self.is_paid or self.is_cancelled:
            return False
        return date.today() > self.due_date

    @property
    def days_overdue(self) -> int:
        """Get number of days overdue (0 if not overdue)."""
        if not self.is_overdue or self.due_date is None:
            return 0
        return (date.today() - self.due_date).days

    def calculate_total(self) -> Money:
        """
        Calculate total from amount, tax, and discount.

        Returns:
            Calculated total amount
        """
        if not self.amount:
            # Calculate from items
            items_total = sum((item.total for item in self.items), Money.zero(self.total_amount.currency))
            base = items_total
        else:
            base = self.amount

        total = base + self.tax_amount - self.discount_amount
        return total

    def mark_as_paid(self, payment_method: str, paid_at: datetime | None = None) -> None:
        """
        Mark transaction as paid.

        Args:
            payment_method: Payment method used
            paid_at: Payment timestamp (defaults to now)

        Raises:
            InvalidStateTransitionError: If already paid or cancelled
        """
        if self.is_paid:
            raise InvalidStateTransitionError(self.payment_status, "completed")

        if self.is_cancelled:
            raise InvalidStateTransitionError(self.payment_status, "completed")

        self.payment_status = "completed"
        self.payment_method = payment_method
        self.paid_at = paid_at or datetime.utcnow()
        self.mark_as_updated()

    def mark_as_failed(self, reason: str | None = None) -> None:
        """
        Mark transaction payment as failed.

        Args:
            reason: Optional failure reason
        """
        if self.is_cancelled:
            raise InvalidStateTransitionError(self.payment_status, "failed")

        self.payment_status = "failed"
        if reason:
            self.extra_metadata["failure_reason"] = reason
        self.mark_as_updated()

    def cancel(self, cancelled_by: UUID, reason: str | None = None) -> None:
        """
        Cancel the transaction.

        Args:
            cancelled_by: User who cancelled the transaction
            reason: Optional cancellation reason

        Raises:
            InvalidStateTransitionError: If already completed or refunded
        """
        if self.payment_status in ["completed", "refunded"]:
            raise InvalidStateTransitionError(self.payment_status, "cancelled")

        self.payment_status = "cancelled"
        self.cancelled_at = datetime.utcnow()
        self.cancelled_by = cancelled_by

        if reason:
            self.extra_metadata["cancellation_reason"] = reason

        self.mark_as_updated()

    def refund(self, reason: str | None = None) -> None:
        """
        Refund the transaction.

        Args:
            reason: Refund reason

        Raises:
            InvalidStateTransitionError: If not completed
        """
        if not self.is_paid:
            raise InvalidStateTransitionError(self.payment_status, "refunded")

        self.payment_status = "refunded"
        if reason:
            self.extra_metadata["refund_reason"] = reason
        self.mark_as_updated()

    def add_item(self, item: TransactionItem) -> None:
        """
        Add a line item to the transaction.

        Args:
            item: Transaction item to add
        """
        # Validate currency matches
        if item.total.currency != self.total_amount.currency:
            raise ValidationError(
                f"Item currency {item.total.currency} doesn't match transaction currency {self.total_amount.currency}"
            )

        self.items.append(item)
        self.mark_as_updated()

    def set_mercadopago_details(
        self,
        payment_id: str | None = None,
        payment_link: str | None = None,
        preference_id: str | None = None,
    ) -> None:
        """
        Set MercadoPago payment details.

        Args:
            payment_id: MercadoPago payment ID
            payment_link: Payment link URL
            preference_id: Preference ID
        """
        if payment_id:
            self.mercadopago_payment_id = payment_id
        if payment_link:
            self.mercadopago_payment_link = payment_link
        if preference_id:
            self.mercadopago_preference_id = preference_id
        self.mark_as_updated()

    def set_invoice_pdf(self, pdf_path: str) -> None:
        """
        Set the invoice PDF path.

        Args:
            pdf_path: Path to generated PDF
        """
        self.invoice_pdf_path = pdf_path
        self.mark_as_updated()

    def mark_invoice_sent(self, sent_at: datetime | None = None) -> None:
        """
        Mark invoice as sent.

        Args:
            sent_at: Sent timestamp (defaults to now)
        """
        self.invoice_sent_at = sent_at or datetime.utcnow()
        self.mark_as_updated()

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Transaction(id={self.id}, number='{self.transaction_number}', "
            f"type='{self.transaction_type}', total={self.total_amount}, status='{self.payment_status}')>"
        )
