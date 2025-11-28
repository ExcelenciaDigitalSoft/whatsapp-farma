"""Interfaces for Plex ERP integration services."""
from typing import Protocol

from .base import IExternalService


class IPlexService(IExternalService, Protocol):
    """Contract for Plex 25 API clients.

    The Plex API exposes multiple GET endpoints under `/ws/<resource>` and a
    POST endpoint at `/ws` that receives the requested method name in the body.
    Implementations should translate the low-level HTTP details and return the
    `content` section of the Plex response on success.
    """

    async def get(self, method: str, params: dict | None = None) -> dict:
        """Call a Plex GET endpoint using the configured prefix."""

    async def post(self, method: str, content: dict | None = None) -> dict:
        """Call a Plex POST endpoint sending the body in `request.content`."""

    async def close(self) -> None:
        """Release any network resources (e.g., close HTTP clients)."""
