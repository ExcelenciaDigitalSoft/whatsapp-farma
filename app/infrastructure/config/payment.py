"""Payment gateway configuration."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PaymentConfig(BaseSettings):
    """
    Payment gateway integration configuration.

    Follows Open/Closed Principle - can support multiple payment providers
    (MercadoPago, Stripe, PayPal, etc.) through configuration, not code changes.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="PAYMENT_"
    )

    # Provider Configuration
    provider: str = Field(
        default="mercadopago",
        description="Payment provider (mercadopago, stripe, paypal)"
    )

    # MercadoPago Configuration
    mercadopago_access_token: str | None = Field(
        default=None,
        description="MercadoPago access token",
        alias="MERCADOPAGO_ACCESS_TOKEN"
    )
    mercadopago_public_key: str | None = Field(
        default=None,
        description="MercadoPago public key",
        alias="MERCADOPAGO_PUBLIC_KEY"
    )
    mercadopago_webhook_secret: str | None = Field(
        default=None,
        description="MercadoPago webhook secret for signature validation",
        alias="MERCADOPAGO_WEBHOOK_SECRET"
    )

    # General Payment Settings
    currency: str = Field(default="ARS", description="Default currency (ARS, USD, etc.)")
    timeout: int = Field(default=30, description="Payment API request timeout in seconds")
    max_retries: int = Field(default=3, description="Max retry attempts for failed requests")

    # Transaction Settings
    enable_refunds: bool = Field(default=True, description="Enable refund functionality")
    auto_capture: bool = Field(
        default=True,
        description="Automatically capture payments (vs. manual capture)"
    )
    payment_expiration_minutes: int = Field(
        default=60,
        description="Payment link expiration in minutes"
    )

    # Webhook Configuration
    webhook_url: str | None = Field(
        default=None,
        description="Webhook URL for payment notifications"
    )
    webhook_enabled: bool = Field(default=True, description="Enable webhook processing")

    # Limits
    min_payment_amount: float = Field(
        default=100.0,
        description="Minimum payment amount in currency"
    )
    max_payment_amount: float = Field(
        default=1000000.0,
        description="Maximum payment amount in currency"
    )

    @property
    def is_configured(self) -> bool:
        """Check if payment gateway is properly configured."""
        if self.provider.lower() == "mercadopago":
            return bool(self.mercadopago_access_token and self.mercadopago_public_key)
        return False

    @property
    def is_mercadopago(self) -> bool:
        """Check if using MercadoPago provider."""
        return self.provider.lower() == "mercadopago"

    @property
    def is_stripe(self) -> bool:
        """Check if using Stripe provider."""
        return self.provider.lower() == "stripe"

    def validate_amount(self, amount: float) -> bool:
        """Validate if payment amount is within limits."""
        return self.min_payment_amount <= amount <= self.max_payment_amount
