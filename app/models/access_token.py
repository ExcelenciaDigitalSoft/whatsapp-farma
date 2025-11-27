"""
Access Token model - API Authentication tokens with role-based access control.
"""
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from uuid import UUID as UUID_Type
import uuid as uuid_module

from app.db.base import Base


class AccessToken(Base):
    """
    Access Token model for API authentication.

    Supports:
    - Role-based access control (admin, manager, readonly, limited)
    - Scope-based permissions
    - Rate limiting per token
    - IP whitelisting (optional)
    - Token expiration
    - Usage tracking
    """

    __tablename__: str = "access_tokens"  # type: ignore[assignment]

    # Primary Key
    id: Mapped[UUID_Type] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_module.uuid4)

    # Foreign Key to Pharmacy
    pharmacy_id: Mapped[UUID_Type] = mapped_column(UUID(as_uuid=True), ForeignKey("pharmacies.id", ondelete="CASCADE"), nullable=False, index=True)

    # Token Details
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)  # SHA-256 hash
    token_name: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Human-readable name

    # Permissions & Scope
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # admin, manager, readonly, limited
    scopes: Mapped[List] = mapped_column(JSONB, default=[], nullable=False)  # ["clients:read", "transactions:write", etc.]

    # Rate Limiting
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    rate_limit_per_day: Mapped[int] = mapped_column(Integer, default=10000, nullable=False)

    # IP Restrictions (optional - empty array means all IPs allowed)
    allowed_ips: Mapped[List] = mapped_column(JSONB, default=[], nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)  # NULL = never expires
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    created_by: Mapped[UUID_Type | None] = mapped_column(UUID(as_uuid=True), nullable=True)  # User/admin who created it
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by: Mapped[UUID_Type | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Extra metadata (flexible JSON storage)
    extra_metadata: Mapped[dict] = mapped_column(JSONB, default={}, nullable=False)

    # Relationships
    pharmacy = relationship("Pharmacy", back_populates="access_tokens")
    audit_logs = relationship("AuditLog", foreign_keys="[AuditLog.token_id]", back_populates="token")

    # Constraints
    __table_args__ = (
        CheckConstraint(role.in_(["admin", "manager", "readonly", "limited"]), name="chk_token_role"),
    )

    def __repr__(self):
        return f"<AccessToken(id={self.id}, pharmacy_id={self.pharmacy_id}, role='{self.role}', active={self.is_active})>"

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
