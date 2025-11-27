"""Chattigo WhatsApp adapter implementation."""
import httpx

from app.domain.interfaces.services import INotificationService
from app.domain.exceptions import ServiceUnavailableError
from app.infrastructure.config import WhatsAppConfig


class ChattigoAdapter(INotificationService):
    """
    Adapter for Chattigo WhatsApp API.

    Implements INotificationService interface to send WhatsApp messages
    through the Chattigo platform.

    This adapter follows the Adapter Pattern, translating between
    our domain interface and the Chattigo API.
    """

    def __init__(self, config: WhatsAppConfig):
        """
        Initialize Chattigo adapter.

        Args:
            config: WhatsApp configuration
        """
        self._config = config
        self._client = httpx.AsyncClient(
            base_url=config.api_url,
            headers={"Authorization": f"Bearer {config.auth_token}"},
            timeout=config.timeout
        )

    async def send_message(
        self,
        recipient: str,
        message: str,
        **kwargs
    ) -> bool:
        """
        Send a WhatsApp message.

        Args:
            recipient: Phone number (normalized format)
            message: Message text
            **kwargs: Additional parameters

        Returns:
            True if sent successfully

        Raises:
            ServiceUnavailableError: If service is not available
        """
        if not self._config.is_configured:
            raise ServiceUnavailableError("WhatsApp service not configured")

        try:
            response = await self._client.post(
                "/messages",
                json={
                    "phone": recipient,
                    "body": message,
                    "from": self._config.whatsapp_number,
                }
            )
            response.raise_for_status()
            return True

        except httpx.HTTPError as e:
            raise ServiceUnavailableError(f"Failed to send WhatsApp message: {str(e)}")

    async def send_template_message(
        self,
        recipient: str,
        template_id: str,
        parameters: dict,
        **kwargs
    ) -> bool:
        """
        Send a templated WhatsApp message.

        Args:
            recipient: Phone number
            template_id: Template identifier
            parameters: Template parameters
            **kwargs: Additional parameters

        Returns:
            True if sent successfully
        """
        if not self._config.is_configured:
            raise ServiceUnavailableError("WhatsApp service not configured")

        try:
            response = await self._client.post(
                "/templates",
                json={
                    "phone": recipient,
                    "template": template_id,
                    "params": parameters,
                    "from": self._config.whatsapp_number,
                }
            )
            response.raise_for_status()
            return True

        except httpx.HTTPError as e:
            raise ServiceUnavailableError(f"Failed to send template message: {str(e)}")

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()
