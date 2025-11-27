"""WhatsApp service configuration."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WhatsAppConfig(BaseSettings):
    """
    WhatsApp integration configuration.

    Designed following Open/Closed Principle - extensible for different providers
    (Chattigo, Twilio, official WhatsApp Business API, etc.) without modification.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="WHATSAPP_"
    )

    # Provider Configuration
    provider: str = Field(
        default="chattigo",
        description="WhatsApp service provider (chattigo, twilio, official)"
    )

    # Chattigo-specific settings
    api_url: str = Field(
        default="https://api.chattigo.com/v1",
        description="WhatsApp provider API base URL",
        alias="CHATTIGO_API_URL"
    )
    auth_token: str | None = Field(
        default=None,
        description="WhatsApp provider authentication token",
        alias="CHATTIGO_AUTH_TOKEN"
    )
    whatsapp_number: str | None = Field(
        default=None,
        description="Pharmacy WhatsApp number",
        alias="CHATTIGO_WHATSAPP_NUMBER"
    )

    # General WhatsApp settings
    timeout: int = Field(default=30, description="API request timeout in seconds")
    max_retries: int = Field(default=3, description="Max retry attempts for failed requests")
    retry_delay: int = Field(default=1, description="Delay between retries in seconds")

    # Rate limiting
    rate_limit_per_minute: int = Field(
        default=100,
        description="Max messages per minute to prevent spam"
    )

    # Message settings
    enable_read_receipts: bool = Field(default=True, description="Enable read receipts")
    enable_typing_indicator: bool = Field(default=True, description="Show typing indicator")

    @property
    def is_configured(self) -> bool:
        """Check if WhatsApp service is properly configured."""
        return bool(self.auth_token and self.whatsapp_number)

    @property
    def is_chattigo(self) -> bool:
        """Check if using Chattigo provider."""
        return self.provider.lower() == "chattigo"

    @property
    def is_twilio(self) -> bool:
        """Check if using Twilio provider."""
        return self.provider.lower() == "twilio"
