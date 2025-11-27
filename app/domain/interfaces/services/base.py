"""Base service interfaces for domain and external services."""
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable


class IDomainService(ABC):
    """
    Base interface for domain services.

    Domain services encapsulate business logic that:
    - Doesn't naturally fit within a single entity
    - Requires coordination between multiple entities
    - Represents a significant domain concept

    Domain services should be stateless and contain only business logic,
    without any infrastructure concerns.
    """
    pass


@runtime_checkable
class IExternalService(Protocol):
    """
    Protocol for external service integrations.

    This protocol defines the contract for services that integrate with
    external systems (APIs, third-party services, etc.).

    Using Protocol allows for structural subtyping (duck typing with type hints)
    without requiring explicit inheritance.
    """

    async def is_available(self) -> bool:
        """
        Check if the external service is available.

        Returns:
            True if the service is reachable and operational, False otherwise
        """
        ...


class INotificationService(ABC):
    """Interface for notification services (WhatsApp, SMS, Email, etc.)."""

    @abstractmethod
    async def send_message(
        self,
        recipient: str,
        message: str,
        **kwargs
    ) -> bool:
        """
        Send a message to a recipient.

        Args:
            recipient: The recipient identifier (phone, email, etc.)
            message: The message content
            **kwargs: Additional service-specific parameters

        Returns:
            True if message was sent successfully, False otherwise

        Raises:
            ServiceUnavailableError: If the service is not available
        """
        pass

    @abstractmethod
    async def send_template_message(
        self,
        recipient: str,
        template_id: str,
        parameters: dict,
        **kwargs
    ) -> bool:
        """
        Send a templated message to a recipient.

        Args:
            recipient: The recipient identifier
            template_id: The template identifier
            parameters: Template parameters
            **kwargs: Additional service-specific parameters

        Returns:
            True if message was sent successfully, False otherwise
        """
        pass


class IPaymentGateway(ABC):
    """Interface for payment gateway integrations."""

    @abstractmethod
    async def create_payment(
        self,
        amount: float,
        currency: str,
        description: str,
        metadata: dict | None = None
    ) -> dict:
        """
        Create a payment intent/order.

        Args:
            amount: Payment amount
            currency: Currency code (e.g., "ARS", "USD")
            description: Payment description
            metadata: Additional payment metadata

        Returns:
            Payment data including payment_id and payment_url

        Raises:
            PaymentGatewayError: If payment creation fails
        """
        pass

    @abstractmethod
    async def get_payment_status(self, payment_id: str) -> dict:
        """
        Get the status of a payment.

        Args:
            payment_id: The payment identifier

        Returns:
            Payment status data

        Raises:
            PaymentNotFoundError: If payment doesn't exist
        """
        pass

    @abstractmethod
    async def refund_payment(
        self,
        payment_id: str,
        amount: float | None = None
    ) -> dict:
        """
        Refund a payment (full or partial).

        Args:
            payment_id: The payment identifier
            amount: Amount to refund (None for full refund)

        Returns:
            Refund data

        Raises:
            PaymentGatewayError: If refund fails
        """
        pass


class IDocumentGenerator(ABC):
    """Interface for document generation services (PDF, receipts, invoices)."""

    @abstractmethod
    async def generate_invoice(
        self,
        invoice_data: dict,
        output_path: str | None = None
    ) -> bytes:
        """
        Generate an invoice document.

        Args:
            invoice_data: Invoice information
            output_path: Optional file path to save the document

        Returns:
            The generated document as bytes

        Raises:
            DocumentGenerationError: If document generation fails
        """
        pass

    @abstractmethod
    async def generate_receipt(
        self,
        receipt_data: dict,
        output_path: str | None = None
    ) -> bytes:
        """
        Generate a receipt document.

        Args:
            receipt_data: Receipt information
            output_path: Optional file path to save the document

        Returns:
            The generated document as bytes
        """
        pass
