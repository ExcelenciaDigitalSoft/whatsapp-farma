"""Pharmacy repository interface."""
from abc import abstractmethod

from .base import IRepository
from app.domain.entities import Pharmacy
from app.domain.value_objects import TaxId


class IPharmacyRepository(IRepository[Pharmacy, dict, dict]):
    """
    Pharmacy repository interface.

    Extends the base repository with pharmacy-specific query methods.
    """

    @abstractmethod
    async def find_by_tax_id(self, tax_id: TaxId) -> Pharmacy | None:
        """
        Find a pharmacy by tax ID (CUIT).

        Args:
            tax_id: Tax identification number

        Returns:
            Pharmacy if found, None otherwise
        """
        pass

    @abstractmethod
    async def find_active(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> list[Pharmacy]:
        """
        Find all active pharmacies.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of active pharmacies
        """
        pass

    @abstractmethod
    async def find_by_subscription_plan(
        self,
        plan: str,
        skip: int = 0,
        limit: int = 100
    ) -> list[Pharmacy]:
        """
        Find pharmacies by subscription plan.

        Args:
            plan: Subscription plan name
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of pharmacies with the plan
        """
        pass

    @abstractmethod
    async def find_with_whatsapp_enabled(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> list[Pharmacy]:
        """
        Find pharmacies with WhatsApp enabled.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of pharmacies with WhatsApp enabled
        """
        pass

    @abstractmethod
    async def count_active(self) -> int:
        """
        Count active pharmacies.

        Returns:
            Number of active pharmacies
        """
        pass
