"""Base repository interface following Repository Pattern."""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

# Type variable for entity types
EntityT = TypeVar("EntityT")
CreateSchemaT = TypeVar("CreateSchemaT")
UpdateSchemaT = TypeVar("UpdateSchemaT")


class IRepository(ABC, Generic[EntityT, CreateSchemaT, UpdateSchemaT]):
    """
    Generic repository interface defining standard CRUD operations.

    This interface follows the Repository Pattern and provides a consistent
    abstraction layer between the domain and data access layers.

    Type Parameters:
        EntityT: The domain entity type
        CreateSchemaT: The schema for creating new entities
        UpdateSchemaT: The schema for updating existing entities
    """

    @abstractmethod
    async def create(self, data: CreateSchemaT) -> EntityT:
        """
        Create a new entity.

        Args:
            data: The creation schema with entity data

        Returns:
            The created entity

        Raises:
            DomainException: If creation fails due to business rules
        """
        pass

    @abstractmethod
    async def find_by_id(self, entity_id: UUID) -> EntityT | None:
        """
        Find an entity by its unique identifier.

        Args:
            entity_id: The unique identifier of the entity

        Returns:
            The entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: dict | None = None
    ) -> list[EntityT]:
        """
        Retrieve all entities with optional pagination and filtering.

        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Optional dictionary of filter criteria

        Returns:
            List of entities matching the criteria
        """
        pass

    @abstractmethod
    async def update(self, entity_id: UUID, data: UpdateSchemaT) -> EntityT | None:
        """
        Update an existing entity.

        Args:
            entity_id: The unique identifier of the entity to update
            data: The update schema with new entity data

        Returns:
            The updated entity if found, None otherwise

        Raises:
            DomainException: If update fails due to business rules
        """
        pass

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """
        Delete an entity by its unique identifier.

        Args:
            entity_id: The unique identifier of the entity to delete

        Returns:
            True if the entity was deleted, False if not found
        """
        pass

    @abstractmethod
    async def exists(self, entity_id: UUID) -> bool:
        """
        Check if an entity exists by its unique identifier.

        Args:
            entity_id: The unique identifier to check

        Returns:
            True if the entity exists, False otherwise
        """
        pass

    @abstractmethod
    async def count(self, filters: dict | None = None) -> int:
        """
        Count entities matching optional filter criteria.

        Args:
            filters: Optional dictionary of filter criteria

        Returns:
            Number of entities matching the criteria
        """
        pass
