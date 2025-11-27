"""Application-level configuration settings."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApplicationConfig(BaseSettings):
    """
    Core application configuration.

    Handles application-level settings like name, version, environment, and server configuration.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="APP_"
    )

    # Application Metadata
    name: str = Field(
        default="WhatsApp Pharmacy Assistant",
        description="Application name",
        alias="APP_NAME"
    )
    version: str = Field(
        default="v1",
        description="API version",
        alias="API_VERSION"
    )
    description: str = Field(
        default="WhatsApp Pharmacy Billing and Payment Assistant",
        description="Application description"
    )

    # Environment Configuration
    environment: str = Field(
        default="development",
        description="Environment: development, staging, production",
        alias="ENVIRONMENT"
    )
    debug: bool = Field(
        default=True,
        description="Enable debug mode",
        alias="DEBUG"
    )

    # Server Configuration
    host: str = Field(
        default="0.0.0.0",
        description="Server host",
        alias="HOST"
    )
    port: int = Field(
        default=3019,
        description="Server port",
        alias="PORT"
    )
    workers: int = Field(
        default=1,
        description="Number of worker processes"
    )
    reload: bool = Field(
        default=True,
        description="Enable auto-reload on code changes"
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format"
    )
    enable_request_logging: bool = Field(
        default=True,
        description="Enable HTTP request logging"
    )

    # Performance Settings
    max_request_size: int = Field(
        default=10485760,  # 10 MB
        description="Maximum request size in bytes"
    )
    timeout_seconds: int = Field(
        default=60,
        description="Request timeout in seconds"
    )

    # Feature Flags
    enable_swagger: bool = Field(
        default=True,
        description="Enable Swagger/OpenAPI documentation"
    )
    enable_metrics: bool = Field(
        default=True,
        description="Enable application metrics"
    )
    enable_health_check: bool = Field(
        default=True,
        description="Enable health check endpoints"
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.environment.lower() == "staging"

    @property
    def server_url(self) -> str:
        """Get the full server URL."""
        protocol = "https" if self.is_production else "http"
        if self.port in [80, 443]:
            return f"{protocol}://{self.host}"
        return f"{protocol}://{self.host}:{self.port}"
