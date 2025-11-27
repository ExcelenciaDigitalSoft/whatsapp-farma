"""
Pharmacy model - Multi-tenant master table.
"""
from sqlalchemy import String, Boolean, DateTime, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from uuid import UUID as UUID_Type
import uuid as uuid_module

from app.db.base import Base


class Pharmacy(Base):
    """
    Pharmacy model for multi-tenant system.

    Each pharmacy represents a separate tenant with isolated data.
    """

    __tablename__: str = "pharmacies"  # type: ignore[assignment]

    # Primary Key
    id: Mapped[UUID_Type] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_module.uuid4)

    # Business Information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tax_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)  # CUIT/CUIL

    # Contact Information
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Address
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(2), default="AR")

    # WhatsApp Configuration
    whatsapp_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    whatsapp_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Business Settings
    currency: Mapped[str] = mapped_column(String(3), default="ARS")
    timezone: Mapped[str] = mapped_column(String(50), default="America/Argentina/Buenos_Aires")

    # Status
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # active, suspended, inactive
    subscription_plan: Mapped[str | None] = mapped_column(String(50), nullable=True)  # free, basic, premium

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Settings (flexible JSON storage)
    settings: Mapped[dict] = mapped_column(JSONB, default={}, nullable=False)

    # Relationships
    access_tokens = relationship("AccessToken", back_populates="pharmacy", cascade="all, delete-orphan")
    clients = relationship("Client", back_populates="pharmacy", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="pharmacy", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="pharmacy", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint(status.in_(["active", "suspended", "inactive"]), name="chk_pharmacy_status"),
    )

    def __repr__(self):
        return f"<Pharmacy(id={self.id}, name='{self.name}', status='{self.status}')>"
