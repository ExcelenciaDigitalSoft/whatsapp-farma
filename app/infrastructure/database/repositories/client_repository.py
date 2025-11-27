"""Client repository implementation with SQLAlchemy."""
from uuid import UUID
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces.repositories import IClientRepository
from app.domain.entities import Client
from app.domain.value_objects import Phone
from app.models.client import Client as ClientModel
from app.infrastructure.database.mappers.client_mapper import ClientMapper


class ClientRepository(IClientRepository):
    """
    SQLAlchemy implementation of IClientRepository.

    Handles persistence of Client entities using SQLAlchemy models
    and provides query methods for client data access.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session
        self._mapper = ClientMapper()

    async def create(self, data: Client) -> Client:
        """Create a new client."""
        model = self._mapper.to_model(data)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return self._mapper.to_entity(model)

    async def find_by_id(self, entity_id: UUID) -> Client | None:
        """Find client by ID."""
        result = await self._session.execute(
            select(ClientModel).where(ClientModel.id == entity_id)
        )
        model = result.scalar_one_or_none()
        return self._mapper.to_entity(model) if model else None

    async def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: dict | None = None
    ) -> list[Client]:
        """Find all clients with pagination."""
        query = select(ClientModel).offset(skip).limit(limit)

        if filters:
            if "pharmacy_id" in filters:
                query = query.where(ClientModel.pharmacy_id == filters["pharmacy_id"])
            if "status" in filters:
                query = query.where(ClientModel.status == filters["status"])

        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._mapper.to_entity(model) for model in models]

    async def update(self, entity_id: UUID, data: Client) -> Client | None:
        """Update an existing client."""
        result = await self._session.execute(
            select(ClientModel).where(ClientModel.id == entity_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            return None

        self._mapper.update_model_from_entity(model, data)
        await self._session.commit()
        await self._session.refresh(model)
        return self._mapper.to_entity(model)

    async def delete(self, entity_id: UUID) -> bool:
        """Delete a client (soft delete)."""
        result = await self._session.execute(
            select(ClientModel).where(ClientModel.id == entity_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            return False

        # Soft delete
        from datetime import datetime
        model.deleted_at = datetime.utcnow()
        await self._session.commit()
        return True

    async def exists(self, entity_id: UUID) -> bool:
        """Check if client exists."""
        result = await self._session.execute(
            select(func.count()).select_from(ClientModel).where(ClientModel.id == entity_id)
        )
        count = result.scalar()
        return bool(count and count > 0)

    async def count(self, filters: dict | None = None) -> int:
        """Count clients."""
        query = select(func.count()).select_from(ClientModel)

        if filters:
            if "pharmacy_id" in filters:
                query = query.where(ClientModel.pharmacy_id == filters["pharmacy_id"])
            if "status" in filters:
                query = query.where(ClientModel.status == filters["status"])

        result = await self._session.execute(query)
        count = result.scalar()
        return count if count is not None else 0

    # Client-specific methods

    async def find_by_phone(
        self,
        phone: Phone,
        pharmacy_id: UUID
    ) -> Client | None:
        """Find client by phone number within a pharmacy."""
        result = await self._session.execute(
            select(ClientModel).where(
                ClientModel.pharmacy_id == pharmacy_id,
                ClientModel.phone_normalized == phone.normalized
            )
        )
        model = result.scalar_one_or_none()
        return self._mapper.to_entity(model) if model else None

    async def find_by_pharmacy(
        self,
        pharmacy_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Client]:
        """Find all clients for a pharmacy."""
        result = await self._session.execute(
            select(ClientModel)
            .where(ClientModel.pharmacy_id == pharmacy_id)
            .offset(skip)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._mapper.to_entity(model) for model in models]

    async def find_active_by_pharmacy(
        self,
        pharmacy_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Client]:
        """Find active clients for a pharmacy."""
        result = await self._session.execute(
            select(ClientModel)
            .where(
                ClientModel.pharmacy_id == pharmacy_id,
                ClientModel.status == "active"
            )
            .offset(skip)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._mapper.to_entity(model) for model in models]

    async def find_with_debt(
        self,
        pharmacy_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Client]:
        """Find clients with outstanding debt."""
        result = await self._session.execute(
            select(ClientModel)
            .where(
                ClientModel.pharmacy_id == pharmacy_id,
                ClientModel.current_balance < 0
            )
            .offset(skip)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._mapper.to_entity(model) for model in models]

    async def find_by_tag(
        self,
        tag: str,
        pharmacy_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Client]:
        """Find clients by tag."""
        result = await self._session.execute(
            select(ClientModel)
            .where(
                ClientModel.pharmacy_id == pharmacy_id,
                ClientModel.tags.contains([tag])
            )
            .offset(skip)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._mapper.to_entity(model) for model in models]

    async def search(
        self,
        query: str,
        pharmacy_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Client]:
        """Search clients by name, phone, or email."""
        search_pattern = f"%{query}%"
        result = await self._session.execute(
            select(ClientModel)
            .where(
                ClientModel.pharmacy_id == pharmacy_id,
                or_(
                    ClientModel.first_name.ilike(search_pattern),
                    ClientModel.last_name.ilike(search_pattern),
                    ClientModel.full_name.ilike(search_pattern),
                    ClientModel.phone.ilike(search_pattern),
                    ClientModel.email.ilike(search_pattern)
                )
            )
            .offset(skip)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._mapper.to_entity(model) for model in models]

    async def count_by_pharmacy(self, pharmacy_id: UUID) -> int:
        """Count clients for a pharmacy."""
        result = await self._session.execute(
            select(func.count()).select_from(ClientModel).where(
                ClientModel.pharmacy_id == pharmacy_id
            )
        )
        count = result.scalar()
        return count if count is not None else 0

    async def get_next_external_id(self, pharmacy_id: UUID) -> int:
        """Get next available external ID for a pharmacy."""
        result = await self._session.execute(
            select(func.max(ClientModel.external_id)).where(
                ClientModel.pharmacy_id == pharmacy_id
            )
        )
        max_id = result.scalar()
        return int(max_id) + 1 if max_id else 1
