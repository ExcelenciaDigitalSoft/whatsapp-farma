"""
Authentication service for token management and validation.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import hashlib
import secrets
import uuid

from app.models.access_token import AccessToken
from app.models.pharmacy import Pharmacy
from app.core.config import settings


class AuthService:
    """Service for managing authentication tokens."""

    @staticmethod
    def generate_token() -> str:
        """
        Generate a cryptographically secure random token.

        Returns:
            str: 32-character hexadecimal token
        """
        return secrets.token_hex(32)

    @staticmethod
    def hash_token(token: str) -> str:
        """
        Hash a token with SHA-256.

        Args:
            token: Plain text token

        Returns:
            str: SHA-256 hash of the token
        """
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    async def create_token(
        db: AsyncSession,
        pharmacy_id: uuid.UUID,
        token_name: str,
        role: str,
        scopes: list[str] | None = None,
        expires_in_days: int | None = None,
        created_by: uuid.UUID | None = None,
    ) -> tuple[AccessToken, str]:
        """
        Create a new access token for a pharmacy.

        Args:
            db: Database session
            pharmacy_id: Pharmacy UUID
            token_name: Human-readable name for the token
            role: Role (admin, manager, readonly, limited)
            scopes: List of permission scopes
            expires_in_days: Number of days until expiration (None = never expires)
            created_by: UUID of user/admin creating the token

        Returns:
            tuple: (AccessToken model, plain text token)

        Note:
            The plain text token is only returned once and must be saved by the caller.
            It cannot be retrieved later.
        """
        # Generate token
        plain_token = AuthService.generate_token()
        token_hash = AuthService.hash_token(plain_token)

        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # Create token record
        access_token = AccessToken(
            pharmacy_id=pharmacy_id,
            token_hash=token_hash,
            token_name=token_name,
            role=role,
            scopes=scopes or [],
            expires_at=expires_at,
            created_by=created_by,
        )

        db.add(access_token)
        await db.commit()
        await db.refresh(access_token)

        return access_token, plain_token

    @staticmethod
    async def validate_token(
        db: AsyncSession,
        token: str
    ) -> tuple[AccessToken, Pharmacy] | None:
        """
        Validate a token and return the associated access token and pharmacy.

        Args:
            db: Database session
            token: Plain text token

        Returns:
            tuple: (AccessToken, Pharmacy) if valid, None if invalid
        """
        token_hash = AuthService.hash_token(token)

        result = await db.execute(
            select(AccessToken, Pharmacy)
            .join(Pharmacy, AccessToken.pharmacy_id == Pharmacy.id)
            .where(AccessToken.token_hash == token_hash)
            .where(AccessToken.is_active == True)
        )
        row = result.first()

        if not row:
            return None

        access_token, pharmacy = row

        # Check if token is expired
        if access_token.is_expired:
            return None

        # Check if pharmacy is active
        if pharmacy.status != "active":
            return None

        return access_token, pharmacy

    @staticmethod
    async def revoke_token(
        db: AsyncSession,
        token_id: uuid.UUID,
        revoked_by: uuid.UUID | None = None
    ) -> bool:
        """
        Revoke an access token.

        Args:
            db: Database session
            token_id: Token UUID to revoke
            revoked_by: UUID of user/admin revoking the token

        Returns:
            bool: True if revoked successfully, False if not found
        """
        result = await db.execute(
            select(AccessToken).where(AccessToken.id == token_id)
        )
        token = result.scalar_one_or_none()

        if not token:
            return False

        token.is_active = False
        token.revoked_at = datetime.utcnow()
        token.revoked_by = revoked_by

        await db.commit()
        return True

    @staticmethod
    async def list_tokens(
        db: AsyncSession,
        pharmacy_id: uuid.UUID,
        active_only: bool = True
    ) -> list[AccessToken]:
        """
        List all tokens for a pharmacy.

        Args:
            db: Database session
            pharmacy_id: Pharmacy UUID
            active_only: If True, only return active tokens

        Returns:
            list: List of AccessToken objects
        """
        query = select(AccessToken).where(AccessToken.pharmacy_id == pharmacy_id)

        if active_only:
            query = query.where(AccessToken.is_active == True)

        result = await db.execute(query.order_by(AccessToken.created_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def check_permission(
        token: AccessToken,
        required_scope: str
    ) -> bool:
        """
        Check if a token has a specific permission scope.

        Args:
            token: AccessToken object
            required_scope: Required scope (e.g., "clients:write")

        Returns:
            bool: True if token has permission
        """
        # Admin role has all permissions
        if token.role == "admin":
            return True

        # Check if scope is in token's scopes
        return required_scope in token.scopes
