"""Repository interfaces."""
from .base import IRepository
from .client_repository import IClientRepository
from .pharmacy_repository import IPharmacyRepository
from .transaction_repository import ITransactionRepository

__all__ = [
    "IRepository",
    "IClientRepository",
    "IPharmacyRepository",
    "ITransactionRepository",
]
