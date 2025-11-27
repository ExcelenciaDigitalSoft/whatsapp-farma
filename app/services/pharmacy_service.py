"""
Pharmacy service for managing pharmacy accounts.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.models.pharmacy import Pharmacy


class PharmacyService:
    """Service for managing pharmacy accounts."""

    @staticmethod
    async def create_pharmacy(
        db: AsyncSession,
        name: str,
        tax_id: str,
        **kwargs
    ) -> Pharmacy:
        """
        Create a new pharmacy.

        Args:
            db: Database session
            name: Pharmacy name
            tax_id: Tax ID (CUIT/CUIL)
            **kwargs: Additional pharmacy fields

        Returns:
            Pharmacy: Created pharmacy object
        """
        pharmacy = Pharmacy(
            name=name,
            tax_id=tax_id,
            **kwargs
        )

        db.add(pharmacy)
        await db.commit()
        await db.refresh(pharmacy)

        return pharmacy

    @staticmethod
    async def get_pharmacy(
        db: AsyncSession,
        pharmacy_id: uuid.UUID
    ) -> Pharmacy | None:
        """
        Get pharmacy by ID.

        Args:
            db: Database session
            pharmacy_id: Pharmacy UUID

        Returns:
            Pharmacy or None if not found
        """
        result = await db.execute(
            select(Pharmacy)
            .where(Pharmacy.id == pharmacy_id)
            .where(Pharmacy.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_pharmacy_by_tax_id(
        db: AsyncSession,
        tax_id: str
    ) -> Pharmacy | None:
        """
        Get pharmacy by tax ID.

        Args:
            db: Database session
            tax_id: Tax ID (CUIT/CUIL)

        Returns:
            Pharmacy or None if not found
        """
        result = await db.execute(
            select(Pharmacy)
            .where(Pharmacy.tax_id == tax_id)
            .where(Pharmacy.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_pharmacy(
        db: AsyncSession,
        pharmacy_id: uuid.UUID,
        **updates
    ) -> Pharmacy | None:
        """
        Update pharmacy information.

        Args:
            db: Database session
            pharmacy_id: Pharmacy UUID
            **updates: Fields to update

        Returns:
            Updated Pharmacy or None if not found
        """
        pharmacy = await PharmacyService.get_pharmacy(db, pharmacy_id)
        if not pharmacy:
            return None

        for key, value in updates.items():
            if hasattr(pharmacy, key):
                setattr(pharmacy, key, value)

        await db.commit()
        await db.refresh(pharmacy)

        return pharmacy

    @staticmethod
    async def update_pharmacy_status(
        db: AsyncSession,
        pharmacy_id: uuid.UUID,
        status: str
    ) -> Pharmacy | None:
        """
        Update pharmacy status.

        Args:
            db: Database session
            pharmacy_id: Pharmacy UUID
            status: New status (active, suspended, inactive)

        Returns:
            Updated Pharmacy or None if not found
        """
        return await PharmacyService.update_pharmacy(
            db,
            pharmacy_id,
            status=status
        )

    @staticmethod
    async def list_pharmacies(
        db: AsyncSession,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[Pharmacy]:
        """
        List pharmacies with optional filtering.

        Args:
            db: Database session
            status: Filter by status (active, suspended, inactive)
            limit: Max results to return
            offset: Number of results to skip

        Returns:
            list: List of Pharmacy objects
        """
        query = select(Pharmacy).where(Pharmacy.deleted_at.is_(None))

        if status:
            query = query.where(Pharmacy.status == status)

        query = query.order_by(Pharmacy.created_at.desc()).limit(limit).offset(offset)

        result = await db.execute(query)
        return list(result.scalars().all())
