"""Client repository interface."""
from abc import abstractmethod
from uuid import UUID

from .base import IRepository
from app.domain.entities import Client
from app.domain.value_objects import Phone


class IClientRepository(IRepository[Client, Client, Client]):
    """
    Client repository interface.

    Extends the base repository with client-specific query methods.
    """

    @abstractmethod
    async def find_by_phone(
        self,
        phone: Phone,
        pharmacy_id: UUID
    ) -> Client | None:
        """
        Find a client by phone number within a pharmacy.

        Args:
            phone: Client phone number
            pharmacy_id: Pharmacy ID for multi-tenant isolation

        Returns:
            Client if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_by_pharmacy(
        self,
        pharmacy_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Client]:
        """
        Find all clients for a pharmacy.

        Args:
            pharmacy_id: Pharmacy ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of clients
        """
        pass

    @abstractmethod
    async def find_active_by_pharmacy(
        self,
        pharmacy_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Client]:
        """
        Find active clients for a pharmacy.

        Args:
            pharmacy_id: Pharmacy ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of active clients
        """
        pass

    @abstractmethod
    async def find_with_debt(
        self,
        pharmacy_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Client]:
        """
        Find clients with outstanding debt.

        Args:
            pharmacy_id: Pharmacy ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of clients with negative balance
        """
        pass

    @abstractmethod
    async def find_by_tag(
        self,
        tag: str,
        pharmacy_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Client]:
        """
        Find clients by tag.

        Args:
            tag: Tag to search for
            pharmacy_id: Pharmacy ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of clients with the tag
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        pharmacy_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Client]:
        """
        Search clients by name, phone, or email.

        Args:
            query: Search query
            pharmacy_id: Pharmacy ID
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of matching clients
        """
        pass

    @abstractmethod
    async def count_by_pharmacy(self, pharmacy_id: UUID) -> int:
        """
        Count clients for a pharmacy.

        Args:
            pharmacy_id: Pharmacy ID

        Returns:
            Number of clients
        """
        pass

    @abstractmethod
    async def get_next_external_id(self, pharmacy_id: UUID) -> int:
        """
        Get next available external ID for a pharmacy.

        Args:
            pharmacy_id: Pharmacy ID

        Returns:
            Next sequential ID
        """
        pass
