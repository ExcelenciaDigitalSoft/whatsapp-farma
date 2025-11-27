"""
Audit Log model - Security, compliance, and activity tracking.
"""
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from uuid import UUID as UUID_Type
import uuid as uuid_module

from app.db.base import Base


class AuditLog(Base):
    """
    Audit Log model for tracking all system events.

    Supports:
    - Event tracking (CRUD operations, authentication, etc.)
    - Actor tracking (who did what)
    - Change tracking (before/after values)
    - Request metadata (IP, user agent, etc.)
    - Security and compliance auditing
    """

    __tablename__: str = "audit_logs"  # type: ignore[assignment]

    # Primary Key
    id: Mapped[UUID_Type] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_module.uuid4)

    # Foreign Key to Pharmacy (optional - some events may not have pharmacy context)
    pharmacy_id: Mapped[UUID_Type | None] = mapped_column(UUID(as_uuid=True), ForeignKey("pharmacies.id", ondelete="CASCADE"), nullable=True, index=True)

    # Event Details
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # client.created, transaction.paid, etc.
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # client, transaction, invoice
    entity_id: Mapped[UUID_Type | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    # Actor Information
    actor_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # token, user, system
    actor_id: Mapped[UUID_Type | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    token_id: Mapped[UUID_Type | None] = mapped_column(UUID(as_uuid=True), ForeignKey("access_tokens.id"), nullable=True, index=True)

    # Request Details
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)  # PostgreSQL INET type for IP addresses
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Change Tracking
    old_values: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # Snapshot before change
    new_values: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # Snapshot after change

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

    # Extra metadata (flexible JSON storage)
    extra_metadata: Mapped[dict] = mapped_column(JSONB, default={}, nullable=False)

    # Relationships
    pharmacy = relationship("Pharmacy", back_populates="audit_logs")
    token = relationship("AccessToken", foreign_keys=[token_id], back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, event='{self.event_type}', entity='{self.entity_type}', actor='{self.actor_type}')>"
