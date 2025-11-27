"""
Unified application settings combining all configuration modules.

This module follows the Single Responsibility Principle by delegating
specific configuration concerns to specialized modules, while providing
a convenient unified interface.
"""
from functools import lru_cache
from .application import ApplicationConfig
from .database import DatabaseConfig
from .whatsapp import WhatsAppConfig
from .payment import PaymentConfig
from .ai import AIConfig
from .security import SecurityConfig
from .storage import StorageConfig


class Settings:
    """
    Unified settings combining all configuration modules.

    This class provides a convenient single point of access to all configuration
    while maintaining separation of concerns through composition.

    Example:
        >>> settings = get_settings()
        >>> print(settings.app.name)
        >>> print(settings.database.url)
        >>> print(settings.whatsapp.is_configured)
    """

    def __init__(self):
        """Initialize all configuration modules."""
        self.app = ApplicationConfig()
        self.database = DatabaseConfig()
        self.whatsapp = WhatsAppConfig()
        self.payment = PaymentConfig()
        self.ai = AIConfig()
        self.security = SecurityConfig()
        self.storage = StorageConfig()

        # Ensure storage directories exist
        if self.storage.is_local_storage:
            self.storage.ensure_directories()

    @property
    def is_production(self) -> bool:
        """Convenience property for production environment check."""
        return self.app.is_production

    @property
    def is_development(self) -> bool:
        """Convenience property for development environment check."""
        return self.app.is_development

    @property
    def debug(self) -> bool:
        """Convenience property for debug mode check."""
        return self.app.debug

    def validate_configuration(self) -> dict[str, list[str]]:
        """
        Validate all configuration modules and return any issues.

        Returns:
            Dictionary with configuration module names as keys and
            lists of validation issues as values
        """
        issues = {}

        # Validate Database
        if not self.database.url:
            issues.setdefault("database", []).append("Database URL not configured")

        # Validate WhatsApp
        if not self.whatsapp.is_configured:
            issues.setdefault("whatsapp", []).append(
                "WhatsApp service not configured (missing auth_token or whatsapp_number)"
            )

        # Validate Payment
        if not self.payment.is_configured:
            issues.setdefault("payment", []).append(
                "Payment gateway not configured (missing credentials)"
            )

        # Validate Security (production checks)
        if self.is_production and not self.security.is_production_ready:
            issues.setdefault("security", []).append(
                "Security configuration not production-ready"
            )

        # Validate AI (optional)
        if self.ai.enable_langchain and not self.ai.is_configured:
            issues.setdefault("ai", []).append(
                "LangChain enabled but OpenAI API key not configured"
            )

        return issues

    def get_configuration_summary(self) -> dict:
        """
        Get a summary of current configuration status.

        Returns:
            Dictionary with configuration status information
        """
        return {
            "environment": self.app.environment,
            "debug": self.app.debug,
            "database": {
                "type": "PostgreSQL" if self.database.is_postgresql else "SQLite",
                "mongodb_enabled": bool(self.database.mongodb_uri),
                "redis_enabled": bool(self.database.redis_url),
            },
            "integrations": {
                "whatsapp_configured": self.whatsapp.is_configured,
                "whatsapp_provider": self.whatsapp.provider,
                "payment_configured": self.payment.is_configured,
                "payment_provider": self.payment.provider,
                "ai_enabled": self.ai.is_enabled,
            },
            "storage": {
                "type": self.storage.storage_type,
                "pdf_path": self.storage.pdf_storage_path,
            },
            "security": {
                "production_ready": self.security.is_production_ready,
                "cors_origins": len(self.security.allowed_origins),
            },
        }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses LRU cache to ensure singleton pattern and avoid
    re-reading environment variables on every call.

    Returns:
        Cached Settings instance
    """
    return Settings()


# Global settings instance for backward compatibility
settings = get_settings()
