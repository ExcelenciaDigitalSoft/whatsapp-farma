"""Base entity class for domain entities."""
from datetime import datetime
from uuid import UUID, uuid4
from dataclasses import dataclass, field


@dataclass
class BaseEntity:
    """
    Base class for all domain entities.

    Provides common attributes and behavior for all entities:
    - Unique identifier (UUID)
    - Timestamps for auditing
    - Soft delete support

    All domain entities should inherit from this class.
    """

    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = None

    def mark_as_deleted(self) -> None:
        """Soft delete the entity."""
        self.deleted_at = datetime.utcnow()

    def is_deleted(self) -> bool:
        """Check if entity is soft deleted."""
        return self.deleted_at is not None

    def mark_as_updated(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()

    def __eq__(self, other: object) -> bool:
        """Compare entities by ID."""
        if not isinstance(other, BaseEntity):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash by ID."""
        return hash(self.id)
