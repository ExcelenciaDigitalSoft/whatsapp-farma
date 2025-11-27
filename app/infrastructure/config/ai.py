"""AI service configuration."""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AIConfig(BaseSettings):
    """
    AI/ML service configuration (OpenAI, LangChain, etc.).

    Optional configuration for AI-powered features like intelligent query responses.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="AI_"
    )

    # OpenAI Configuration
    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key for general queries",
        alias="OPENAI_API_KEY"
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model to use",
        alias="OPENAI_MODEL"
    )
    openai_temperature: float = Field(
        default=0.7,
        description="Model temperature (0.0-1.0)"
    )
    openai_max_tokens: int = Field(
        default=500,
        description="Maximum tokens per response"
    )

    # LangChain Configuration
    enable_langchain: bool = Field(
        default=False,
        description="Enable LangChain for advanced AI features"
    )
    langchain_verbose: bool = Field(
        default=False,
        description="Enable verbose logging for LangChain"
    )

    # ChromaDB Configuration (Vector Database)
    chroma_persist_directory: str = Field(
        default="./chroma_db",
        description="ChromaDB persistence directory"
    )
    chroma_collection_name: str = Field(
        default="pharmacy_knowledge",
        description="ChromaDB collection name"
    )

    # General AI Settings
    timeout: int = Field(default=30, description="AI API request timeout in seconds")
    max_retries: int = Field(default=2, description="Max retry attempts for failed requests")
    enable_caching: bool = Field(
        default=True,
        description="Enable response caching to reduce API calls"
    )
    cache_ttl_hours: int = Field(
        default=24,
        description="Cache time-to-live in hours"
    )

    @property
    def is_configured(self) -> bool:
        """Check if AI service is properly configured."""
        return bool(self.openai_api_key)

    @property
    def is_enabled(self) -> bool:
        """Check if AI features are enabled."""
        return self.is_configured
