"""Transaction DTOs for application layer."""
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from typing import Any


@dataclass
class TransactionItemDTO:
    """DTO for transaction line item."""

    name: str
    quantity: int
    unit_price: Decimal
    total: Decimal


@dataclass
class CreateTransactionDTO:
    """DTO for creating a new transaction."""

    pharmacy_id: UUID
    client_id: UUID
    transaction_type: str  # invoice, payment, credit_note, debit_note
    amount: Decimal
    currency: str = "ARS"
    tax_amount: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    payment_method: str | None = None
    description: str | None = None
    items: list[TransactionItemDTO] | None = None
    transaction_date: date | None = None
    due_date: date | None = None
    extra_metadata: dict[str, Any] | None = None

    def __post_init__(self):
        """Initialize default values."""
        if self.items is None:
            self.items = []
        if self.extra_metadata is None:
            self.extra_metadata = {}
        if self.transaction_date is None:
            self.transaction_date = date.today()


@dataclass
class ProcessPaymentDTO:
    """DTO for processing a payment."""

    transaction_id: UUID
    payment_method: str  # cash, transfer, mercadopago
    amount: Decimal | None = None  # If None, pays full amount
    paid_at: datetime | None = None


@dataclass
class TransactionResponseDTO:
    """DTO for transaction response."""

    id: UUID
    pharmacy_id: UUID
    client_id: UUID
    transaction_number: str
    transaction_type: str
    amount: Decimal
    currency: str
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    payment_method: str | None
    payment_status: str
    description: str | None
    items: list[dict[str, Any]]
    mercadopago_payment_id: str | None
    mercadopago_payment_link: str | None
    invoice_pdf_path: str | None
    transaction_date: date
    due_date: date | None
    paid_at: datetime | None
    is_paid: bool
    is_overdue: bool
    days_overdue: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, transaction) -> "TransactionResponseDTO":
        """
        Create DTO from Transaction entity.

        Args:
            transaction: Transaction entity

        Returns:
            TransactionResponseDTO
        """
        return cls(
            id=transaction.id,
            pharmacy_id=transaction.pharmacy_id,
            client_id=transaction.client_id,
            transaction_number=transaction.transaction_number,
            transaction_type=transaction.transaction_type,
            amount=transaction.amount.amount if transaction.amount else transaction.total_amount.amount,
            currency=transaction.total_amount.currency,
            tax_amount=transaction.tax_amount.amount,
            discount_amount=transaction.discount_amount.amount,
            total_amount=transaction.total_amount.amount,
            payment_method=transaction.payment_method,
            payment_status=transaction.payment_status,
            description=transaction.description,
            items=[
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit_price": float(item.unit_price.amount),
                    "total": float(item.total.amount),
                }
                for item in transaction.items
            ],
            mercadopago_payment_id=transaction.mercadopago_payment_id,
            mercadopago_payment_link=transaction.mercadopago_payment_link,
            invoice_pdf_path=transaction.invoice_pdf_path,
            transaction_date=transaction.transaction_date,
            due_date=transaction.due_date,
            paid_at=transaction.paid_at,
            is_paid=transaction.is_paid,
            is_overdue=transaction.is_overdue,
            days_overdue=transaction.days_overdue,
            created_at=transaction.created_at,
            updated_at=transaction.updated_at,
        )


@dataclass
class TransactionListDTO:
    """DTO for paginated list of transactions."""

    transactions: list[TransactionResponseDTO]
    total: int
    skip: int
    limit: int

    @property
    def has_more(self) -> bool:
        """Check if there are more results."""
        return (self.skip + len(self.transactions)) < self.total
