"""
Application configuration using Pydantic Settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
import secrets


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden by environment variables or .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ============================================
    # APPLICATION SETTINGS
    # ============================================
    APP_NAME: str = "WhatsApp Pharmacy Assistant"
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")
    DEBUG: bool = Field(default=True, description="Enable debug mode")
    API_VERSION: str = Field(default="v1", description="API version")
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32), description="Secret key for JWT")

    # ============================================
    # DATABASE CONFIGURATION
    # ============================================
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://pharmacy_user:pharmacy_pass_2024@localhost:5432/pharmacy_db",
        description="PostgreSQL database URL"
    )

    # MongoDB settings (chat history)
    MONGODB_URI: str = Field(default="mongodb://localhost:27017/", description="MongoDB connection URI")
    MONGODB_DATABASE_NAME: str = Field(default="pharmacy_chat", description="MongoDB database name")
    MONGODB_COLLECTION_NAME: str = Field(default="chat_messages", description="MongoDB collection for messages")

    # Redis settings (cache & rate limiting)
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")

    # ============================================
    # WHATSAPP INTEGRATION (Chattigo)
    # ============================================
    CHATTIGO_API_URL: str = Field(default="https://api.chattigo.com/v1", description="Chattigo API base URL")
    CHATTIGO_AUTH_TOKEN: str | None = Field(default=None, description="Chattigo authentication token")
    CHATTIGO_WHATSAPP_NUMBER: str | None = Field(default=None, description="Pharmacy WhatsApp number")

    # ============================================
    # MERCADO PAGO INTEGRATION
    # ============================================
    MERCADOPAGO_ACCESS_TOKEN: str | None = Field(default=None, description="Mercado Pago access token")
    MERCADOPAGO_PUBLIC_KEY: str | None = Field(default=None, description="Mercado Pago public key")
    MERCADOPAGO_WEBHOOK_SECRET: str | None = Field(default=None, description="Mercado Pago webhook secret")

    # ============================================
    # OPENAI (Optional - for general queries)
    # ============================================
    OPENAI_API_KEY: str | None = Field(default=None, description="OpenAI API key for general queries")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", description="OpenAI model to use")

    # ============================================
    # FILE STORAGE
    # ============================================
    PDF_STORAGE_PATH: str = Field(default="./invoices", description="Path to store invoice PDFs")
    PDF_BASE_URL: str | None = Field(default=None, description="Base URL for accessing PDFs")

    # ============================================
    # SECURITY & RATE LIMITING
    # ============================================
    TOKEN_EXPIRY_DAYS: int = Field(default=90, description="Access token expiry in days")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="Max API requests per minute")
    RATE_LIMIT_PER_DAY: int = Field(default=10000, description="Max API requests per day")

    # JWT settings
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="JWT access token expiry in minutes")

    # ============================================
    # CORS SETTINGS
    # ============================================
    ALLOWED_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:3019"],
        description="Allowed CORS origins"
    )
    ALLOWED_METHODS: list[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Allowed HTTP methods"
    )
    ALLOWED_HEADERS: list[str] = Field(default=["*"], description="Allowed headers")

    # ============================================
    # SERVER SETTINGS
    # ============================================
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=3019, description="Server port")

    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("ALLOWED_METHODS", pre=True)
    def parse_allowed_methods(cls, v):
        """Parse ALLOWED_METHODS from comma-separated string or list."""
        if isinstance(v, str):
            return [method.strip() for method in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"


# Global settings instance
settings = Settings()
