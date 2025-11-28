"""HTTP client adapter for Plex 25 API."""
from __future__ import annotations

import httpx

from app.domain.exceptions import ExternalServiceError, ServiceUnavailableError
from app.domain.interfaces.services import IPlexService
from app.infrastructure.config import PlexConfig


class PlexAdapter(IPlexService):
    """Async client for Plex 25 integration.

    This adapter hides HTTP details (Basic auth, prefixes, response parsing) and
    returns the `content` payload of Plex responses. It follows the Adapter
    pattern so application code only depends on the `IPlexService` contract.
    """

    def __init__(self, config: PlexConfig):
        if not config.is_configured:
            raise ValueError("Plex integration is not properly configured")

        self._config = config
        self._client = httpx.AsyncClient(
            base_url=config.sanitized_base_url,
            auth=(config.username or "", config.password or ""),
            timeout=config.timeout,
            headers={"Content-Type": "application/json"},
            verify=config.verify_ssl,
        )

    async def is_available(self) -> bool:
        """Lightweight availability check using the `usuarios` endpoint."""

        try:
            await self.get("usuarios")
            return True
        except ServiceUnavailableError:
            return False
        except ExternalServiceError:
            # Service reachable but returned error code
            return False

    async def get(self, method: str, params: dict | None = None) -> dict:
        """Call a Plex GET endpoint."""

        url = f"{self._config.get_prefix.rstrip('/')}/{method.lstrip('/')}"
        try:
            response = await self._client.get(url, params=params or {})
        except httpx.HTTPError as exc:  # pragma: no cover - network failure
            raise ServiceUnavailableError(str(exc))

        return self._parse_response(response, method)

    async def post(self, method: str, content: dict | None = None) -> dict:
        """Call a Plex POST endpoint with the expected request envelope."""

        body = {"request": {"type": method, "content": content or {}}}
        try:
            response = await self._client.post(self._config.post_endpoint, json=body)
        except httpx.HTTPError as exc:  # pragma: no cover - network failure
            raise ServiceUnavailableError(str(exc))

        return self._parse_response(response, method)

    async def get_sales(
        self,
        branch_id: str,
        emission_date: str | None = None,
        from_id: str | None = None,
        part_id: str | None = None,
    ) -> dict:
        """Convenience wrapper for `ventas` endpoint."""

        params: dict[str, str] = {"sucursal": branch_id}
        if emission_date:
            params["fecha"] = emission_date
        if from_id:
            params["id"] = from_id
        if part_id:
            params["idparte"] = part_id
        return await self.get("ventas", params=params)

    async def get_clients(
        self,
        client_id: str | None = None,
        cuit: str | None = None,
        since_date: str | None = None,
    ) -> dict:
        """Wrapper for `clientes` endpoint."""

        params: dict[str, str] = {}
        if client_id:
            params["id"] = client_id
        if cuit:
            params["cuit"] = cuit
        if since_date:
            params["fecha_desde"] = since_date
        return await self.get("clientes", params=params)

    async def get_products(
        self,
        search: str | None = None,
        change_date: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        **filters,
    ) -> dict:
        """Wrapper for `productos` endpoint with pagination and filters."""

        params: dict[str, str | int] = {}
        if search:
            params["busqueda"] = search
        if change_date:
            params["fechacambio"] = change_date
        if page:
            params["paginanro"] = page
        if page_size:
            params["paginacant"] = page_size

        for key, value in filters.items():
            if value is not None:
                params[key] = value

        return await self.get("productos", params=params)

    async def get_stock(self, branch_id: str, page: int = 1) -> dict:
        """Wrapper for `stock` endpoint."""

        return await self.get("stock", params={"sucursal": branch_id, "pagina": page})

    async def close(self) -> None:
        """Close the underlying HTTP client."""

        await self._client.aclose()

    def _parse_response(self, response: httpx.Response, method: str) -> dict:
        """Validate HTTP status and Plex response envelope."""

        try:
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:  # pragma: no cover - httpx already validated
            raise ServiceUnavailableError(f"Invalid response from Plex: {exc}")

        content = payload.get("response")
        if not content:
            raise ExternalServiceError(f"Malformed response for method '{method}'")

        resp_code = content.get("respcode")
        if resp_code is None:
            raise ExternalServiceError(f"Missing respcode for method '{method}'")
        if str(resp_code) != "0":
            raise ExternalServiceError(content.get("respmsg") or f"Error code {resp_code}")

        return content.get("content", {})
