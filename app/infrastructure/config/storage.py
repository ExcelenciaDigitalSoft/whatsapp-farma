"""File storage configuration."""
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageConfig(BaseSettings):
    """
    File storage configuration for documents, PDFs, and uploads.

    Handles file storage settings for invoices, receipts, and other documents.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="STORAGE_"
    )

    # PDF Storage Configuration
    pdf_storage_path: str = Field(
        default="./invoices",
        description="Path to store invoice PDFs",
        alias="PDF_STORAGE_PATH"
    )
    pdf_base_url: str | None = Field(
        default=None,
        description="Base URL for accessing PDFs",
        alias="PDF_BASE_URL"
    )

    # Upload Configuration
    upload_directory: str = Field(
        default="./uploads",
        description="Directory for file uploads"
    )
    max_upload_size: int = Field(
        default=10485760,  # 10 MB
        description="Maximum upload size in bytes"
    )
    allowed_extensions: list[str] = Field(
        default=["pdf", "png", "jpg", "jpeg", "xlsx", "csv"],
        description="Allowed file extensions for uploads"
    )

    # Storage Type
    storage_type: str = Field(
        default="local",
        description="Storage type (local, s3, azure, gcs)"
    )

    # S3 Configuration (Optional)
    s3_bucket: str | None = Field(
        default=None,
        description="S3 bucket name"
    )
    s3_region: str | None = Field(
        default=None,
        description="S3 region"
    )
    s3_access_key: str | None = Field(
        default=None,
        description="S3 access key"
    )
    s3_secret_key: str | None = Field(
        default=None,
        description="S3 secret key"
    )

    # File Retention
    retention_days: int = Field(
        default=365,
        description="Number of days to retain files"
    )
    enable_auto_cleanup: bool = Field(
        default=False,
        description="Enable automatic cleanup of old files"
    )

    @property
    def is_local_storage(self) -> bool:
        """Check if using local file system storage."""
        return self.storage_type.lower() == "local"

    @property
    def is_s3_storage(self) -> bool:
        """Check if using S3 storage."""
        return self.storage_type.lower() == "s3"

    @property
    def pdf_storage_dir(self) -> Path:
        """Get PDF storage directory as Path object."""
        return Path(self.pdf_storage_path)

    @property
    def upload_dir(self) -> Path:
        """Get upload directory as Path object."""
        return Path(self.upload_directory)

    def ensure_directories(self) -> None:
        """Ensure storage directories exist."""
        if self.is_local_storage:
            self.pdf_storage_dir.mkdir(parents=True, exist_ok=True)
            self.upload_dir.mkdir(parents=True, exist_ok=True)

    def is_allowed_extension(self, filename: str) -> bool:
        """Check if file extension is allowed."""
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        return extension in self.allowed_extensions
