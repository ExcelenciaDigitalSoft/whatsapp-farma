"""
Pydantic schemas for Transaction model.
"""
from pydantic import BaseModel, Field
from datetime import datetime, date
from decimal import Decimal
import uuid


class TransactionItemCreate(BaseModel):
    """Schema for transaction line item."""
    name: str
    quantity: int = 1
    unit_price: Decimal
    total: Decimal


class TransactionCreate(BaseModel):
    """Schema for creating a transaction."""
    client_id: uuid.UUID
    transaction_type: str = Field(..., description="invoice, payment, credit_note, debit_note")
    amount: Decimal
    tax_amount: Decimal | None = Decimal("0")
    discount_amount: Decimal | None = Decimal("0")
    payment_method: str | None = None
    description: str | None = None
    items: list[dict] | None = []
    due_date: date | None = None


class TransactionResponse(BaseModel):
    """Schema for transaction response."""
    id: uuid.UUID
    pharmacy_id: uuid.UUID
    client_id: uuid.UUID
    transaction_number: str
    transaction_type: str
    amount: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    payment_method: str | None
    payment_status: str
    transaction_date: date
    due_date: date | None
    paid_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Schema for paginated transaction list."""
    data: list[TransactionResponse]
    total: int
    limit: int
    offset: int
