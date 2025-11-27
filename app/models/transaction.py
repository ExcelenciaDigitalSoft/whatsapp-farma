"""
Transaction model - Billing, payments, invoices, credit/debit notes.
"""
from decimal import Decimal
from sqlalchemy import String, DateTime, Text, ForeignKey, DECIMAL, Date, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime, date
from uuid import UUID as UUID_Type
import uuid as uuid_module

from app.db.base import Base


class Transaction(Base):
    """
    Transaction model for all financial operations.

    Supports:
    - Invoices, payments, credit notes, debit notes
    - Mercado Pago integration
    - PDF invoice generation
    - Payment tracking
    - Multi-currency (primarily ARS)
    """

    __tablename__: str = "transactions"  # type: ignore[assignment]

    # Primary Key
    id: Mapped[UUID_Type] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_module.uuid4)

    # Foreign Keys
    pharmacy_id: Mapped[UUID_Type] = mapped_column(UUID(as_uuid=True), ForeignKey("pharmacies.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id: Mapped[UUID_Type] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="RESTRICT"), nullable=False, index=True)

    # Transaction Details
    transaction_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)  # Auto-generated
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)  # invoice, payment, credit_note, debit_note

    # Amounts
    amount: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="ARS", nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), default=0, nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), default=0, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)

    # Payment Details
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)  # cash, transfer, mercadopago, credit_card
    payment_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending, completed, failed, cancelled, refunded

    # Mercado Pago Integration
    mercadopago_payment_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    mercadopago_payment_link: Mapped[str | None] = mapped_column(Text, nullable=True)
    mercadopago_preference_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Description & Line Items
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    items: Mapped[List] = mapped_column(JSONB, default=[], nullable=False)  # [{"name": "...", "quantity": 1, "unit_price": 10.00, "total": 10.00}]

    # Invoice Details
    invoice_pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    invoice_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Dates
    transaction_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False, index=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_by: Mapped[UUID_Type | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Extra metadata (flexible JSON storage)
    extra_metadata: Mapped[dict] = mapped_column(JSONB, default={}, nullable=False)

    # Relationships
    pharmacy = relationship("Pharmacy", back_populates="transactions")
    client = relationship("Client", back_populates="transactions")
    invoices = relationship("Invoice", back_populates="transaction", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            transaction_type.in_(["invoice", "payment", "credit_note", "debit_note"]),
            name="chk_transaction_type"
        ),
        CheckConstraint(
            payment_status.in_(["pending", "completed", "failed", "cancelled", "refunded"]),
            name="chk_payment_status"
        ),
    )

    def __repr__(self):
        return f"<Transaction(id={self.id}, number='{self.transaction_number}', type='{self.transaction_type}', total={self.total_amount})>"

    @property
    def is_paid(self) -> bool:
        """Check if transaction has been paid."""
        return self.payment_status == "completed"

    @property
    def is_overdue(self) -> bool:
        """Check if transaction is overdue."""
        if self.due_date is None or self.is_paid:
            return False
        return date.today() > self.due_date
