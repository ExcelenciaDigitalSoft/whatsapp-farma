"""Client domain entity."""
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from .base import BaseEntity
from app.domain.value_objects import Phone, Email, Address, TaxId, ClientBalance, Money
from app.domain.exceptions import ValidationError, CreditLimitExceededError


@dataclass(kw_only=True)
class Client(BaseEntity):
    """
    Client domain entity representing a pharmacy customer.

    This is a pure domain entity focused on business logic,
    completely independent of infrastructure concerns like database.

    Attributes:
        pharmacy_id: Pharmacy this client belongs to (multi-tenancy)
        phone: Client phone number
        first_name: Client first name
        last_name: Client last name
        email: Client email address
        tax_id: Tax identification (DNI/CUIT/CUIL)
        address: Physical address
        balance: Financial balance and credit limit
        status: Client status (active, inactive, blocked)
        whatsapp_name: Name from WhatsApp
        whatsapp_opted_in: WhatsApp opt-in status
        last_whatsapp_interaction: Last WhatsApp interaction timestamp
        tags: Flexible tagging system
        notes: Additional notes
        external_id: ID from external system
    """

    pharmacy_id: UUID
    phone: Phone
    balance: ClientBalance
    status: str = "active"

    # Optional personal information
    first_name: str | None = None
    last_name: str | None = None
    email: Email | None = None
    tax_id: TaxId | None = None
    address: Address = field(default_factory=Address.empty)

    # WhatsApp integration
    whatsapp_name: str | None = None
    whatsapp_opted_in: bool = True
    last_whatsapp_interaction: datetime | None = None

    # Metadata
    tags: list[str] = field(default_factory=list)
    notes: str | None = None
    external_id: str | None = None

    def __post_init__(self):
        """Validate client after initialization."""
        self.validate()

    def validate(self) -> None:
        """
        Validate client business rules.

        Raises:
            ValidationError: If validation fails
        """
        if self.status not in ["active", "inactive", "blocked", "suspended"]:
            raise ValidationError(f"Invalid client status: {self.status}")

        if not self.pharmacy_id:
            raise ValidationError("Client must belong to a pharmacy")

    @property
    def full_name(self) -> str | None:
        """Get full name (first + last)."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.whatsapp_name

    @property
    def display_name(self) -> str:
        """Get best available name for display."""
        return self.full_name or str(self.phone) or "Unknown"

    @property
    def owes_money(self) -> bool:
        """Check if client has outstanding debt."""
        return self.balance.is_in_debt

    @property
    def credit_exceeded(self) -> bool:
        """Check if client has exceeded credit limit."""
        return self.balance.is_credit_exceeded

    def can_make_purchase(self, amount: Money) -> bool:
        """
        Check if client can make a purchase.

        Args:
            amount: Purchase amount

        Returns:
            True if purchase is allowed

        Business Rules:
            - Client must be active
            - Purchase must not exceed available credit
        """
        if self.status != "active":
            return False

        return self.balance.can_purchase(amount)

    def apply_charge(self, amount: Money, description: str | None = None) -> None:
        """
        Apply a charge to client account.

        Args:
            amount: Amount to charge
            description: Optional charge description

        Raises:
            ValidationError: If client is not active
            CreditLimitExceededError: If charge would exceed credit limit
        """
        if self.status != "active":
            raise ValidationError(f"Cannot charge inactive client (status: {self.status})")

        if not self.can_make_purchase(amount):
            available = self.balance.available_credit
            raise CreditLimitExceededError(
                f"Charge of {amount} would exceed credit limit. Available credit: {available}"
            )

        self.balance = self.balance.apply_charge(amount)
        self.mark_as_updated()

    def apply_payment(self, amount: Money) -> None:
        """
        Apply a payment to client account.

        Args:
            amount: Payment amount
        """
        self.balance = self.balance.apply_payment(amount)
        self.mark_as_updated()

    def update_credit_limit(self, new_limit: Money) -> None:
        """
        Update client credit limit.

        Args:
            new_limit: New credit limit

        Raises:
            ValidationError: If new limit is invalid
        """
        if new_limit.is_negative():
            raise ValidationError("Credit limit cannot be negative")

        self.balance = self.balance.update_credit_limit(new_limit)
        self.mark_as_updated()

    def activate(self) -> None:
        """Activate the client account."""
        if self.status == "active":
            return

        self.status = "active"
        self.mark_as_updated()

    def deactivate(self) -> None:
        """Deactivate the client account."""
        if self.status == "inactive":
            return

        self.status = "inactive"
        self.mark_as_updated()

    def block(self) -> None:
        """Block the client account (for fraud, non-payment, etc.)."""
        if self.status == "blocked":
            return

        self.status = "blocked"
        self.mark_as_updated()

    def suspend(self) -> None:
        """Suspend the client account (temporary restriction)."""
        if self.status == "suspended":
            return

        self.status = "suspended"
        self.mark_as_updated()

    def update_whatsapp_interaction(self, name: str | None = None) -> None:
        """
        Record a WhatsApp interaction.

        Args:
            name: Optional WhatsApp name to update
        """
        self.last_whatsapp_interaction = datetime.utcnow()
        if name:
            self.whatsapp_name = name
        self.mark_as_updated()

    def opt_in_whatsapp(self) -> None:
        """Opt-in to WhatsApp communications."""
        self.whatsapp_opted_in = True
        self.mark_as_updated()

    def opt_out_whatsapp(self) -> None:
        """Opt-out of WhatsApp communications."""
        self.whatsapp_opted_in = False
        self.mark_as_updated()

    def add_tag(self, tag: str) -> None:
        """Add a tag to the client."""
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.mark_as_updated()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the client."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.mark_as_updated()

    def has_tag(self, tag: str) -> bool:
        """Check if client has a specific tag."""
        return tag in self.tags

    def update_personal_info(
        self,
        first_name: str | None = None,
        last_name: str | None = None,
        email: Email | None = None,
        tax_id: TaxId | None = None,
        address: Address | None = None,
    ) -> None:
        """
        Update client personal information.

        Args:
            first_name: New first name
            last_name: New last name
            email: New email
            tax_id: New tax ID
            address: New address
        """
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
        if email is not None:
            self.email = email
        if tax_id is not None:
            self.tax_id = tax_id
        if address is not None:
            self.address = address

        self.mark_as_updated()

    def __repr__(self) -> str:
        """String representation."""
        return f"<Client(id={self.id}, phone={self.phone}, name='{self.display_name}', status='{self.status}')>"
