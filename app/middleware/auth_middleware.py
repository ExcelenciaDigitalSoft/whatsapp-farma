"""
Authentication middleware for API token validation.
"""
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib

from app.db.session import async_session
from app.models.access_token import AccessToken
from app.models.pharmacy import Pharmacy


security = HTTPBearer(auto_error=False)


class AuthMiddleware:
    """
    Middleware for authenticating API requests using Bearer tokens.

    Flow:
    1. Extract Bearer token from Authorization header
    2. Hash token with SHA-256
    3. Lookup token in database
    4. Validate token (active, not expired, etc.)
    5. Attach pharmacy context to request
    6. Track token usage
    """

    def __init__(self):
        # Public endpoints that don't require authentication
        self.public_paths = [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/webhook/whatsapp",  # WhatsApp webhook (validated separately)
            "/api/v1/payments/webhook",  # Mercado Pago webhook (validated separately)
        ]

    async def __call__(self, request: Request, call_next):
        """Process the request with authentication."""
        # Check if path is public
        if self._is_public_path(request.url.path):
            return await call_next(request)

        # Extract token from header
        token = await self._extract_token(request)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Validate token and get pharmacy context
        async with async_session() as db:
            token_data = await self._validate_token(db, token)
            if not token_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Attach pharmacy and token context to request
            request.state.pharmacy_id = token_data["pharmacy_id"]
            request.state.pharmacy = token_data["pharmacy"]
            request.state.token_id = token_data["token_id"]
            request.state.token_role = token_data["role"]
            request.state.token_scopes = token_data["scopes"]

            # Track token usage (fire and forget)
            await self._track_token_usage(db, token_data["token_id"])

        # Continue with request
        response = await call_next(request)
        return response

    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (doesn't require authentication)."""
        return any(path.startswith(public) for public in self.public_paths)

    async def _extract_token(self, request: Request) -> str | None:
        """Extract Bearer token from Authorization header."""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        if not auth_header.startswith("Bearer "):
            return None

        return auth_header[7:]  # Remove "Bearer " prefix

    async def _validate_token(self, db: AsyncSession, token: str) -> dict | None:
        """
        Validate token and return pharmacy context.

        Returns:
            dict with pharmacy_id, pharmacy, token_id, role, scopes
            None if token is invalid
        """
        # Hash token with SHA-256
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Lookup token in database with pharmacy relationship
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

        return {
            "pharmacy_id": pharmacy.id,
            "pharmacy": pharmacy,
            "token_id": access_token.id,
            "role": access_token.role,
            "scopes": access_token.scopes,
        }

    async def _track_token_usage(self, db: AsyncSession, token_id: str):
        """Track token usage (increment counter, update last_used_at)."""
        from datetime import datetime

        result = await db.execute(
            select(AccessToken).where(AccessToken.id == token_id)
        )
        token = result.scalar_one_or_none()

        if token:
            token.usage_count += 1
            token.last_used_at = datetime.utcnow()
            await db.commit()


async def get_current_pharmacy(request: Request) -> Pharmacy:
    """
    Dependency to get current pharmacy from request context.

    Usage:
        @app.get("/api/v1/clients")
        async def get_clients(pharmacy: Pharmacy = Depends(get_current_pharmacy)):
            print(f"Pharmacy: {pharmacy.name}")
    """
    if not hasattr(request.state, "pharmacy"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return request.state.pharmacy


async def get_current_pharmacy_id(request: Request) -> str:
    """
    Dependency to get current pharmacy ID from request context.

    Usage:
        @app.get("/api/v1/clients")
        async def get_clients(pharmacy_id: str = Depends(get_current_pharmacy_id)):
            print(f"Pharmacy ID: {pharmacy_id}")
    """
    if not hasattr(request.state, "pharmacy_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return request.state.pharmacy_id


def require_role(required_role: str):
    """
    Dependency to require specific role.

    Usage:
        @app.post("/api/v1/admin/tokens")
        async def create_token(
            request: Request,
            _: None = Depends(require_role("admin"))
        ):
            # Only admins can access this
    """
    async def check_role(request: Request):
        if not hasattr(request.state, "token_role"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        role_hierarchy = {
            "admin": 4,
            "manager": 3,
            "readonly": 2,
            "limited": 1,
        }

        user_role_level = role_hierarchy.get(request.state.token_role, 0)
        required_role_level = role_hierarchy.get(required_role, 999)

        if user_role_level < required_role_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )

        return None

    return check_role
