"""
Client service for managing pharmacy customers.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from decimal import Decimal
import uuid

from app.models.client import Client
from app.utils.phone_utils import normalizar_numero_whatsapp as normalize_phone_number


class ClientService:
    """Service for managing pharmacy clients."""

    @staticmethod
    async def create_client(
        db: AsyncSession,
        pharmacy_id: uuid.UUID,
        phone: str,
        **kwargs
    ) -> Client:
        """
        Create a new client.

        Args:
            db: Database session
            pharmacy_id: Pharmacy UUID
            phone: Client phone number
            **kwargs: Additional client fields

        Returns:
            Client: Created client object
        """
        # Normalize phone number
        phone_normalized = normalize_phone_number(phone)

        client = Client(
            pharmacy_id=pharmacy_id,
            phone=phone,
            phone_normalized=phone_normalized,
            **kwargs
        )

        db.add(client)
        await db.commit()
        await db.refresh(client)

        return client

    @staticmethod
    async def get_client(
        db: AsyncSession,
        client_id: uuid.UUID,
        pharmacy_id: uuid.UUID
    ) -> Client | None:
        """
        Get client by ID (scoped to pharmacy).

        Args:
            db: Database session
            client_id: Client UUID
            pharmacy_id: Pharmacy UUID (for multi-tenant isolation)

        Returns:
            Client or None if not found
        """
        result = await db.execute(
            select(Client)
            .where(Client.id == client_id)
            .where(Client.pharmacy_id == pharmacy_id)
            .where(Client.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_client_by_phone(
        db: AsyncSession,
        phone: str,
        pharmacy_id: uuid.UUID
    ) -> Client | None:
        """
        Get client by phone number (scoped to pharmacy).

        Args:
            db: Database session
            phone: Phone number (will be normalized)
            pharmacy_id: Pharmacy UUID

        Returns:
            Client or None if not found
        """
        phone_normalized = normalize_phone_number(phone)

        result = await db.execute(
            select(Client)
            .where(Client.phone_normalized == phone_normalized)
            .where(Client.pharmacy_id == pharmacy_id)
            .where(Client.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_client(
        db: AsyncSession,
        client_id: uuid.UUID,
        pharmacy_id: uuid.UUID,
        **updates
    ) -> Client | None:
        """
        Update client information.

        Args:
            db: Database session
            client_id: Client UUID
            pharmacy_id: Pharmacy UUID (for security)
            **updates: Fields to update

        Returns:
            Updated Client or None if not found
        """
        client = await ClientService.get_client(db, client_id, pharmacy_id)
        if not client:
            return None

        # If phone is being updated, normalize it
        if "phone" in updates:
            updates["phone_normalized"] = normalize_phone_number(updates["phone"])

        for key, value in updates.items():
            if hasattr(client, key):
                setattr(client, key, value)

        client.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(client)

        return client

    @staticmethod
    async def update_client_balance(
        db: AsyncSession,
        client_id: uuid.UUID,
        pharmacy_id: uuid.UUID,
        amount: float
    ) -> Client | None:
        """
        Update client balance (add or subtract).

        Args:
            db: Database session
            client_id: Client UUID
            pharmacy_id: Pharmacy UUID
            amount: Amount to add (positive) or subtract (negative)

        Returns:
            Updated Client or None if not found
        """
        client = await ClientService.get_client(db, client_id, pharmacy_id)
        if not client:
            return None

        client.current_balance += Decimal(str(amount))
        client.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(client)

        return client

    @staticmethod
    async def update_whatsapp_interaction(
        db: AsyncSession,
        client_id: uuid.UUID,
        pharmacy_id: uuid.UUID,
        whatsapp_name: str | None = None
    ) -> Client | None:
        """
        Update WhatsApp interaction timestamp and name.

        Args:
            db: Database session
            client_id: Client UUID
            pharmacy_id: Pharmacy UUID
            whatsapp_name: WhatsApp display name (optional)

        Returns:
            Updated Client or None if not found
        """
        client = await ClientService.get_client(db, client_id, pharmacy_id)
        if not client:
            return None

        client.last_whatsapp_interaction = datetime.utcnow()
        if whatsapp_name:
            client.whatsapp_name = whatsapp_name

        await db.commit()
        await db.refresh(client)

        return client

    @staticmethod
    async def list_clients(
        db: AsyncSession,
        pharmacy_id: uuid.UUID,
        status: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[list[Client], int]:
        """
        List clients for a pharmacy with optional filtering.

        Args:
            db: Database session
            pharmacy_id: Pharmacy UUID
            status: Filter by status (active, inactive, blocked)
            search: Search by name or phone
            limit: Max results to return
            offset: Number of results to skip

        Returns:
            tuple: (list of Client objects, total count)
        """
        # Base query
        query = select(Client).where(
            Client.pharmacy_id == pharmacy_id,
            Client.deleted_at.is_(None)
        )

        # Apply filters
        if status:
            query = query.where(Client.status == status)

        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Client.full_name.ilike(search_term)) |
                (Client.first_name.ilike(search_term)) |
                (Client.last_name.ilike(search_term)) |
                (Client.phone.like(search_term)) |
                (Client.phone_normalized.like(search_term))
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering
        query = query.order_by(Client.created_at.desc()).limit(limit).offset(offset)

        result = await db.execute(query)
        clients = list(result.scalars().all())

        return clients, (total if total is not None else 0)

    @staticmethod
    async def delete_client(
        db: AsyncSession,
        client_id: uuid.UUID,
        pharmacy_id: uuid.UUID
    ) -> bool:
        """
        Soft delete a client.

        Args:
            db: Database session
            client_id: Client UUID
            pharmacy_id: Pharmacy UUID

        Returns:
            bool: True if deleted, False if not found
        """
        client = await ClientService.get_client(db, client_id, pharmacy_id)
        if not client:
            return False

        client.deleted_at = datetime.utcnow()
        client.status = "inactive"

        await db.commit()
        return True

    @staticmethod
    async def get_clients_with_debt(
        db: AsyncSession,
        pharmacy_id: uuid.UUID,
        limit: int = 50
    ) -> list[Client]:
        """
        Get clients with outstanding debt (negative balance).

        Args:
            db: Database session
            pharmacy_id: Pharmacy UUID
            limit: Max results to return

        Returns:
            list: List of Client objects with debt
        """
        result = await db.execute(
            select(Client)
            .where(Client.pharmacy_id == pharmacy_id)
            .where(Client.deleted_at.is_(None))
            .where(Client.current_balance < 0)
            .order_by(Client.current_balance.asc())  # Most debt first
            .limit(limit)
        )
        return list(result.scalars().all())
