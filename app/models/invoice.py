"""
Invoice model - PDF invoice management and tracking.
"""
from sqlalchemy import String, DateTime, Integer, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from uuid import UUID as UUID_Type
import uuid as uuid_module

from app.db.base import Base


class Invoice(Base):
    """
    Invoice model for managing PDF invoices.

    Supports:
    - PDF generation and storage
    - Invoice type classification (A, B, C - Argentina specific)
    - Delivery tracking (WhatsApp, email)
    - View tracking
    """

    __tablename__: str = "invoices"  # type: ignore[assignment]

    # Primary Key
    id: Mapped[UUID_Type] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_module.uuid4)

    # Foreign Key to Transaction
    transaction_id: Mapped[UUID_Type] = mapped_column(UUID(as_uuid=True), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Invoice Details
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    invoice_type: Mapped[str] = mapped_column(String(20), nullable=False)  # A, B, C, etc. (Argentina specific)

    # PDF Storage
    pdf_filename: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pdf_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_url: Mapped[str | None] = mapped_column(Text, nullable=True)  # Public URL if stored in cloud
    pdf_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Generation Details
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    template_used: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Delivery Tracking
    sent_via_whatsapp: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Extra metadata (flexible JSON storage)
    extra_metadata: Mapped[dict] = mapped_column(JSONB, default={}, nullable=False)

    # Relationships
    transaction = relationship("Transaction", back_populates="invoices")

    def __repr__(self):
        return f"<Invoice(id={self.id}, number='{self.invoice_number}', type='{self.invoice_type}')>"

    @property
    def has_been_sent(self) -> bool:
        """Check if invoice has been sent to client."""
        return self.sent_at is not None

    @property
    def has_been_viewed(self) -> bool:
        """Check if invoice has been viewed by client."""
        return self.viewed_at is not None
