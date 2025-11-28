"""Service interfaces."""
from .base import (
    IDomainService,
    IExternalService,
    INotificationService,
    IPaymentGateway,
    IDocumentGenerator,
)
from .plex import IPlexService

__all__ = [
    "IDomainService",
    "IExternalService",
    "INotificationService",
    "IPaymentGateway",
    "IDocumentGenerator",
    "IPlexService",
]
