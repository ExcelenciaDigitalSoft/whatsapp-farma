"""High-level service for interacting with Plex 25 API."""
from __future__ import annotations

from typing import Any

from app.domain.interfaces.services import IPlexService
from app.infrastructure.config import get_settings
from app.infrastructure.external.plex import PlexAdapter


class PlexService:
    """Facade that exposes common Plex operations with sensible defaults."""

    def __init__(self, plex_client: IPlexService | None = None):
        settings = get_settings()
        self._client = plex_client or PlexAdapter(settings.plex)

    async def check_availability(self) -> bool:
        """Return True when Plex API responds successfully."""

        return await self._client.is_available()

    async def get_sales(
        self,
        branch_id: str,
        emission_date: str | None = None,
        from_id: str | None = None,
        part_id: str | None = None,
    ) -> dict[str, Any]:
        return await self._client.get_sales(branch_id, emission_date, from_id, part_id)

    async def get_clients(
        self,
        client_id: str | None = None,
        cuit: str | None = None,
        since_date: str | None = None,
    ) -> dict[str, Any]:
        return await self._client.get_clients(client_id, cuit, since_date)

    async def get_products(
        self,
        search: str | None = None,
        change_date: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        **filters,
    ) -> dict[str, Any]:
        return await self._client.get_products(search, change_date, page, page_size, **filters)

    async def get_stock(self, branch_id: str, page: int = 1) -> dict[str, Any]:
        return await self._client.get_stock(branch_id, page)

    async def get_catalog(self, resource: str, **params) -> dict[str, Any]:
        """Fetch catalog-style endpoints such as bancos, provincias, tarjetas, etc."""

        return await self._client.get(resource, params=params)

    async def call_post_action(self, method: str, content: dict[str, Any] | None = None) -> dict[str, Any]:
        """Invoke a POST action using the Plex request envelope."""

        return await self._client.post(method, content=content)

    async def close(self) -> None:
        await self._client.close()
