"""
SQLAlchemy Base configuration for all models.
"""
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy import MetaData
from typing import Any
import re


def camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case for table names."""
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.

    Features:
    - Automatic table name generation from class name (CamelCase -> snake_case)
    - Consistent metadata configuration
    - Type hints for better IDE support
    """

    # Metadata for all tables
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s"
        }
    )

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return camel_to_snake(cls.__name__)

    def dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
