"""Client DTOs for application layer."""
from dataclasses import dataclass
from uuid import UUID
from datetime import datetime
from decimal import Decimal


@dataclass
class CreateClientDTO:
    """DTO for creating a new client."""

    pharmacy_id: UUID
    phone: str
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    tax_id: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str = "AR"
    credit_limit: Decimal = Decimal("0")
    whatsapp_opted_in: bool = True
    tags: list[str] | None = None
    notes: str | None = None
    external_id: str | None = None

    def __post_init__(self):
        """Initialize default values."""
        if self.tags is None:
            self.tags = []


@dataclass
class UpdateClientDTO:
    """DTO for updating an existing client."""

    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    tax_id: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    credit_limit: Decimal | None = None
    whatsapp_opted_in: bool | None = None
    notes: str | None = None


@dataclass
class ClientResponseDTO:
    """DTO for client response."""

    id: UUID
    pharmacy_id: UUID
    phone: str
    phone_normalized: str
    first_name: str | None
    last_name: str | None
    full_name: str | None
    email: str | None
    tax_id: str | None
    address: str | None
    city: str | None
    state: str | None
    postal_code: str | None
    country: str
    credit_limit: Decimal
    current_balance: Decimal
    available_credit: Decimal
    owes_money: bool
    status: str
    whatsapp_name: str | None
    whatsapp_opted_in: bool
    last_whatsapp_interaction: datetime | None
    tags: list[str]
    notes: str | None
    external_id: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, client) -> "ClientResponseDTO":
        """
        Create DTO from Client entity.

        Args:
            client: Client entity

        Returns:
            ClientResponseDTO
        """
        return cls(
            id=client.id,
            pharmacy_id=client.pharmacy_id,
            phone=str(client.phone),
            phone_normalized=client.phone.normalized,
            first_name=client.first_name,
            last_name=client.last_name,
            full_name=client.full_name,
            email=str(client.email) if client.email else None,
            tax_id=str(client.tax_id) if client.tax_id else None,
            address=client.address.street if client.address else None,
            city=client.address.city if client.address else None,
            state=client.address.state if client.address else None,
            postal_code=client.address.postal_code if client.address else None,
            country=client.address.country if client.address else "AR",
            credit_limit=client.balance.credit_limit.amount,
            current_balance=client.balance.current_balance.amount,
            available_credit=client.balance.available_credit.amount,
            owes_money=client.owes_money,
            status=client.status,
            whatsapp_name=client.whatsapp_name,
            whatsapp_opted_in=client.whatsapp_opted_in,
            last_whatsapp_interaction=client.last_whatsapp_interaction,
            tags=client.tags,
            notes=client.notes,
            external_id=client.external_id,
            created_at=client.created_at,
            updated_at=client.updated_at,
        )


@dataclass
class ClientListDTO:
    """DTO for paginated list of clients."""

    clients: list[ClientResponseDTO]
    total: int
    skip: int
    limit: int

    @property
    def has_more(self) -> bool:
        """Check if there are more results."""
        return (self.skip + len(self.clients)) < self.total
