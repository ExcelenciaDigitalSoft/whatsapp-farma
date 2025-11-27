"""API router configuration for Clean Architecture endpoints."""
from fastapi import APIRouter
from app.presentation.api.v1.clients import router as clients_router

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
api_router.include_router(clients_router)

# Export for use in main.py
__all__ = ["api_router"]
