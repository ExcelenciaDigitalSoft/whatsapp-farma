"""Database configuration settings."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """
    Database configuration for PostgreSQL, MongoDB, and Redis.

    Follows Single Responsibility Principle by handling only database-related settings.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="DB_"
    )

    # PostgreSQL Configuration
    url: str = Field(
        default="postgresql+asyncpg://pharmacy_user:pharmacy_pass_2024@localhost:5432/pharmacy_db",
        description="PostgreSQL database URL",
        alias="DATABASE_URL"
    )
    pool_size: int = Field(default=10, description="Database connection pool size")
    max_overflow: int = Field(default=20, description="Max overflow connections")
    echo: bool = Field(default=False, description="Echo SQL statements (for debugging)")

    # MongoDB Configuration
    mongodb_uri: str = Field(
        default="mongodb://localhost:27017/",
        description="MongoDB connection URI",
        alias="MONGODB_URI"
    )
    mongodb_database_name: str = Field(
        default="pharmacy_chat",
        description="MongoDB database name",
        alias="MONGODB_DATABASE_NAME"
    )
    mongodb_collection_name: str = Field(
        default="chat_messages",
        description="MongoDB collection for messages",
        alias="MONGODB_COLLECTION_NAME"
    )

    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
        alias="REDIS_URL"
    )
    redis_max_connections: int = Field(default=50, description="Max Redis connections")
    redis_decode_responses: bool = Field(default=True, description="Decode Redis responses")

    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        return self.url.startswith("sqlite")

    @property
    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL database."""
        return "postgresql" in self.url
