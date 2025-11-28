"""Plex (ERP) integration configuration."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PlexConfig(BaseSettings):
    """Configuration for Plex 25 HTTP API integration.

    The API uses Basic authentication and exposes GET/POST endpoints under the
    `/ws` namespace. Values are loaded from environment variables prefixed with
    `PLEX_` to keep credentials isolated from other services.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="PLEX_",
    )

    base_url: str = Field(
        default="",
        description="Base URL for Plex API (e.g. https://plex.example.com)",
    )
    username: str | None = Field(default=None, description="Basic auth username")
    password: str | None = Field(default=None, description="Basic auth password")
    get_prefix: str = Field(
        default="/ws",
        description="Path prefix for GET operations (usually /ws)",
    )
    post_endpoint: str = Field(
        default="/ws",
        description="Endpoint path for POST actions",
    )
    timeout: int = Field(default=30, description="HTTP client timeout in seconds")
    verify_ssl: bool = Field(
        default=True,
        description="Whether to verify SSL certificates when connecting",
    )

    @property
    def is_configured(self) -> bool:
        """Return True when mandatory credentials are present."""

        return bool(self.base_url and self.username and self.password)

    @property
    def sanitized_base_url(self) -> str:
        """Return the base URL without trailing slash for safe joins."""

        return self.base_url.rstrip("/")
