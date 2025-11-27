"""
Client model - Pharmacy customers.
"""
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, DECIMAL, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
import uuid as uuid_module
from uuid import UUID as UUID_Type
from decimal import Decimal

from app.db.base import Base


class Client(Base):
    """
    Client model representing pharmacy customers.

    Supports:
    - Multi-tenant isolation (pharmacy_id)
    - Phone-based identification
    - Financial tracking (credit limit, balance)
    - WhatsApp integration
    - Flexible metadata storage
    """

    __tablename__: str = "clients"  # type: ignore[assignment]

    # Primary Key
    id: Mapped[UUID_Type] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_module.uuid4)

    # Foreign Key to Pharmacy (multi-tenant)
    pharmacy_id: Mapped[UUID_Type] = mapped_column(UUID(as_uuid=True), ForeignKey("pharmacies.id", ondelete="CASCADE"), nullable=False, index=True)

    # Client Identification
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  # ID from external system
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    phone_normalized: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # Standardized format for matching

    # Personal Information
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True)  # DNI/CUIT

    # Address
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # WhatsApp Integration
    whatsapp_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    whatsapp_opted_in: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_whatsapp_interaction: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Financial Information
    credit_limit: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), default=0, nullable=False)
    current_balance: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), default=0, nullable=False)  # Negative = owes money

    # Status
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # active, inactive, blocked

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Extra data (flexible JSON storage)
    tags: Mapped[List] = mapped_column(JSONB, default=[], nullable=False)
    extra_metadata: Mapped[dict] = mapped_column(JSONB, default={}, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    pharmacy = relationship("Pharmacy", back_populates="clients")
    transactions = relationship("Transaction", back_populates="client", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        UniqueConstraint("pharmacy_id", "phone_normalized", name="uq_pharmacy_client_phone"),
        CheckConstraint(status.in_(["active", "inactive", "blocked"]), name="chk_client_status"),
    )

    def __repr__(self):
        return f"<Client(id={self.id}, phone='{self.phone}', name='{self.full_name or self.first_name}')>"

    @property
    def owes_money(self) -> bool:
        """Check if client has outstanding debt."""
        return self.current_balance < 0
