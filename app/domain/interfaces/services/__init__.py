"""Service interfaces."""
from .base import (
    IDomainService,
    IExternalService,
    INotificationService,
    IPaymentGateway,
    IDocumentGenerator,
)

__all__ = [
    "IDomainService",
    "IExternalService",
    "INotificationService",
    "IPaymentGateway",
    "IDocumentGenerator",
]
