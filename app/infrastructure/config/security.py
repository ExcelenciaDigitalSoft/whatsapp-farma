"""Security and authentication configuration."""
import secrets
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecurityConfig(BaseSettings):
    """
    Security, authentication, and authorization configuration.

    Handles JWT, CORS, rate limiting, and other security-related settings.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="SECURITY_"
    )

    # JWT Configuration
    secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret key for JWT signing",
        alias="SECRET_KEY"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm",
        alias="JWT_ALGORITHM"
    )
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        description="JWT access token expiry in minutes",
        alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        description="JWT refresh token expiry in days"
    )

    # Token Management
    token_expiry_days: int = Field(
        default=90,
        description="Access token expiry in days",
        alias="TOKEN_EXPIRY_DAYS"
    )

    # CORS Configuration
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:3019"],
        description="Allowed CORS origins",
        alias="ALLOWED_ORIGINS"
    )
    allowed_methods: list[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        description="Allowed HTTP methods",
        alias="ALLOWED_METHODS"
    )
    allowed_headers: list[str] = Field(
        default=["*"],
        description="Allowed headers",
        alias="ALLOWED_HEADERS"
    )
    allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests"
    )

    # Rate Limiting
    rate_limit_per_minute: int = Field(
        default=60,
        description="Max API requests per minute per client",
        alias="RATE_LIMIT_PER_MINUTE"
    )
    rate_limit_per_hour: int = Field(
        default=1000,
        description="Max API requests per hour per client"
    )
    rate_limit_per_day: int = Field(
        default=10000,
        description="Max API requests per day per client",
        alias="RATE_LIMIT_PER_DAY"
    )

    # Password Policy
    min_password_length: int = Field(
        default=8,
        description="Minimum password length"
    )
    require_uppercase: bool = Field(
        default=True,
        description="Require uppercase letter in password"
    )
    require_lowercase: bool = Field(
        default=True,
        description="Require lowercase letter in password"
    )
    require_digit: bool = Field(
        default=True,
        description="Require digit in password"
    )
    require_special_char: bool = Field(
        default=False,
        description="Require special character in password"
    )

    # Security Headers
    enable_security_headers: bool = Field(
        default=True,
        description="Enable security headers (HSTS, CSP, etc.)"
    )
    enable_https_redirect: bool = Field(
        default=False,
        description="Redirect HTTP to HTTPS"
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("allowed_methods", mode="before")
    @classmethod
    def parse_allowed_methods(cls, v):
        """Parse ALLOWED_METHODS from comma-separated string or list."""
        if isinstance(v, str):
            return [method.strip() for method in v.split(",")]
        return v

    @property
    def is_production_ready(self) -> bool:
        """Check if security configuration is production-ready."""
        return (
            len(self.secret_key) >= 32 and
            self.enable_security_headers and
            self.rate_limit_per_minute > 0
        )
