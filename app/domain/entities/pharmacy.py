"""Pharmacy domain entity."""
from dataclasses import dataclass, field
from uuid import UUID
from typing import Any

from .base import BaseEntity
from app.domain.value_objects import Phone, Email, Address, TaxId
from app.domain.exceptions import ValidationError


@dataclass(kw_only=True)
class Pharmacy(BaseEntity):
    """
    Pharmacy domain entity representing a pharmacy tenant.

    Each pharmacy represents a separate tenant with isolated data in a multi-tenant system.

    Attributes:
        name: Business name
        tax_id: Tax identification (CUIT)
        legal_name: Legal business name
        phone: Contact phone
        email: Contact email
        address: Physical address
        whatsapp_number: WhatsApp business number
        whatsapp_enabled: WhatsApp integration status
        currency: Default currency (ISO 4217)
        timezone: Business timezone
        country: Country code (ISO 3166-1)
        status: Pharmacy status (active, suspended, inactive)
        subscription_plan: Subscription level
        settings: Flexible settings storage
    """

    name: str
    tax_id: TaxId
    status: str = "active"

    # Optional business information
    legal_name: str | None = None
    phone: Phone | None = None
    email: Email | None = None
    address: Address = field(default_factory=Address.empty)

    # WhatsApp configuration
    whatsapp_number: Phone | None = None
    whatsapp_enabled: bool = True

    # Business settings
    currency: str = "ARS"
    timezone: str = "America/Argentina/Buenos_Aires"
    country: str = "AR"

    # Subscription
    subscription_plan: str | None = None

    # Flexible settings
    settings: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate pharmacy after initialization."""
        self.validate()

    def validate(self) -> None:
        """
        Validate pharmacy business rules.

        Raises:
            ValidationError: If validation fails
        """
        if not self.name or not self.name.strip():
            raise ValidationError("Pharmacy name cannot be empty")

        if self.status not in ["active", "suspended", "inactive"]:
            raise ValidationError(f"Invalid pharmacy status: {self.status}")

        if len(self.currency) != 3:
            raise ValidationError(f"Invalid currency code: {self.currency}")

        if len(self.country) != 2:
            raise ValidationError(f"Invalid country code: {self.country}")

    @property
    def display_name(self) -> str:
        """Get display name (legal name if available, otherwise name)."""
        return self.legal_name or self.name

    @property
    def is_active(self) -> bool:
        """Check if pharmacy is active."""
        return self.status == "active"

    @property
    def is_suspended(self) -> bool:
        """Check if pharmacy is suspended."""
        return self.status == "suspended"

    @property
    def is_whatsapp_configured(self) -> bool:
        """Check if WhatsApp is properly configured."""
        return self.whatsapp_enabled and self.whatsapp_number is not None

    def activate(self) -> None:
        """Activate the pharmacy."""
        if self.status == "active":
            return

        self.status = "active"
        self.mark_as_updated()

    def suspend(self, reason: str | None = None) -> None:
        """
        Suspend the pharmacy.

        Args:
            reason: Optional suspension reason
        """
        if self.status == "suspended":
            return

        self.status = "suspended"
        if reason:
            self.settings["suspension_reason"] = reason
        self.mark_as_updated()

    def deactivate(self) -> None:
        """Deactivate the pharmacy."""
        if self.status == "inactive":
            return

        self.status = "inactive"
        self.mark_as_updated()

    def enable_whatsapp(self, whatsapp_number: Phone) -> None:
        """
        Enable WhatsApp integration.

        Args:
            whatsapp_number: WhatsApp business number
        """
        self.whatsapp_number = whatsapp_number
        self.whatsapp_enabled = True
        self.mark_as_updated()

    def disable_whatsapp(self) -> None:
        """Disable WhatsApp integration."""
        self.whatsapp_enabled = False
        self.mark_as_updated()

    def update_subscription(self, plan: str) -> None:
        """
        Update subscription plan.

        Args:
            plan: New subscription plan (free, basic, premium)
        """
        valid_plans = ["free", "basic", "premium"]
        if plan not in valid_plans:
            raise ValidationError(f"Invalid subscription plan: {plan}")

        self.subscription_plan = plan
        self.mark_as_updated()

    def update_business_info(
        self,
        name: str | None = None,
        legal_name: str | None = None,
        phone: Phone | None = None,
        email: Email | None = None,
        address: Address | None = None,
    ) -> None:
        """
        Update pharmacy business information.

        Args:
            name: New business name
            legal_name: New legal name
            phone: New phone
            email: New email
            address: New address
        """
        if name is not None:
            if not name.strip():
                raise ValidationError("Pharmacy name cannot be empty")
            self.name = name

        if legal_name is not None:
            self.legal_name = legal_name

        if phone is not None:
            self.phone = phone

        if email is not None:
            self.email = email

        if address is not None:
            self.address = address

        self.mark_as_updated()

    def get_setting(self, key: str, default=None):
        """
        Get a setting value.

        Args:
            key: Setting key
            default: Default value if key not found

        Returns:
            Setting value or default
        """
        return self.settings.get(key, default)

    def set_setting(self, key: str, value) -> None:
        """
        Set a setting value.

        Args:
            key: Setting key
            value: Setting value
        """
        self.settings[key] = value
        self.mark_as_updated()

    def remove_setting(self, key: str) -> None:
        """
        Remove a setting.

        Args:
            key: Setting key
        """
        if key in self.settings:
            del self.settings[key]
            self.mark_as_updated()

    def __repr__(self) -> str:
        """String representation."""
        return f"<Pharmacy(id={self.id}, name='{self.name}', status='{self.status}')>"
