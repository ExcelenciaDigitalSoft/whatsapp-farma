"""
API v1 routes.
"""
from fastapi import APIRouter

from app.api.v1 import clients, transactions, payments, health

# Create main v1 router
api_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(clients.router, prefix="/clients", tags=["Clients"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])

__all__ = ["api_router"]
