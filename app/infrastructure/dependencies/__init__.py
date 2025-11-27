"""Dependency injection system for the application."""
from .container import DependencyContainer, get_container, container
from .database import get_db, get_mongodb, get_redis
from .use_cases import (
    CreateClientUseCaseDep,
    GetClientUseCaseDep,
    CreateTransactionUseCaseDep,
    ProcessPaymentUseCaseDep,
)

__all__ = [
    # Container
    "DependencyContainer",
    "get_container",
    "container",
    # Database
    "get_db",
    "get_mongodb",
    "get_redis",
    # Use Cases
    "CreateClientUseCaseDep",
    "GetClientUseCaseDep",
    "CreateTransactionUseCaseDep",
    "ProcessPaymentUseCaseDep",
]
