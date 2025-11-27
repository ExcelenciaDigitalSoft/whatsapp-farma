"""
Pydantic schemas for Client model.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
import uuid


class ClientCreate(BaseModel):
    """Schema for creating a client."""
    phone: str = Field(..., description="Client phone number")
    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    email: str | None = None
    tax_id: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    credit_limit: Decimal | None = Decimal("0")
    notes: str | None = None


class ClientUpdate(BaseModel):
    """Schema for updating a client."""
    phone: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    email: str | None = None
    tax_id: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    credit_limit: Decimal | None = None
    status: str | None = None
    notes: str | None = None


class ClientResponse(BaseModel):
    """Schema for client response."""
    id: uuid.UUID
    pharmacy_id: uuid.UUID
    phone: str
    phone_normalized: str
    first_name: str | None
    last_name: str | None
    full_name: str | None
    email: str | None
    tax_id: str | None
    current_balance: Decimal
    credit_limit: Decimal
    status: str
    whatsapp_opted_in: bool
    last_whatsapp_interaction: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClientListResponse(BaseModel):
    """Schema for paginated client list."""
    data: list[ClientResponse]
    total: int
    limit: int
    offset: int
