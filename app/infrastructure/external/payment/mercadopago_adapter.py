"""MercadoPago payment gateway adapter."""
import mercadopago

from app.domain.interfaces.services import IPaymentGateway
from app.domain.exceptions import PaymentGatewayError
from app.infrastructure.config import PaymentConfig


class MercadoPagoAdapter(IPaymentGateway):
    """
    Adapter for MercadoPago payment gateway.

    Implements IPaymentGateway interface to process payments
    through MercadoPago platform.

    Follows the Adapter Pattern to decouple payment processing
    from specific gateway implementations.
    """

    def __init__(self, config: PaymentConfig):
        """
        Initialize MercadoPago adapter.

        Args:
            config: Payment configuration
        """
        self._config = config

        if not config.is_configured:
            raise ValueError("MercadoPago not properly configured")

        self._sdk = mercadopago.SDK(config.mercadopago_access_token)

    async def create_payment(
        self,
        amount: float,
        currency: str,
        description: str,
        metadata: dict | None = None
    ) -> dict:
        """
        Create a payment preference.

        Args:
            amount: Payment amount
            currency: Currency code (ARS, USD, etc.)
            description: Payment description
            metadata: Additional metadata

        Returns:
            Payment data with payment_id and payment_url

        Raises:
            PaymentGatewayError: If payment creation fails
        """
        try:
            preference_data = {
                "items": [
                    {
                        "title": description,
                        "quantity": 1,
                        "unit_price": amount,
                        "currency_id": currency,
                    }
                ],
                "back_urls": {
                    "success": metadata.get("success_url") if metadata else None,
                    "failure": metadata.get("failure_url") if metadata else None,
                    "pending": metadata.get("pending_url") if metadata else None,
                },
                "auto_return": "approved",
                "external_reference": metadata.get("external_reference") if metadata else None,
                "metadata": metadata or {},
            }

            result = self._sdk.preference().create(preference_data)

            if result["status"] != 201:
                raise PaymentGatewayError(
                    f"Failed to create payment: {result.get('response', {})}"
                )

            response_data = result["response"]

            return {
                "payment_id": response_data.get("id"),
                "payment_url": response_data.get("init_point"),
                "sandbox_url": response_data.get("sandbox_init_point"),
            }

        except Exception as e:
            raise PaymentGatewayError(f"MercadoPago error: {str(e)}")

    async def get_payment_status(self, payment_id: str) -> dict:
        """
        Get payment status.

        Args:
            payment_id: Payment ID from MercadoPago

        Returns:
            Payment status data

        Raises:
            PaymentGatewayError: If query fails
        """
        try:
            result = self._sdk.payment().get(payment_id)

            if result["status"] != 200:
                raise PaymentGatewayError(f"Failed to get payment status: {payment_id}")

            response_data = result["response"]

            return {
                "payment_id": response_data.get("id"),
                "status": response_data.get("status"),
                "status_detail": response_data.get("status_detail"),
                "transaction_amount": response_data.get("transaction_amount"),
                "currency_id": response_data.get("currency_id"),
                "payment_method_id": response_data.get("payment_method_id"),
                "date_approved": response_data.get("date_approved"),
            }

        except Exception as e:
            raise PaymentGatewayError(f"MercadoPago error: {str(e)}")

    async def refund_payment(
        self,
        payment_id: str,
        amount: float | None = None
    ) -> dict:
        """
        Refund a payment.

        Args:
            payment_id: Payment ID
            amount: Amount to refund (None for full refund)

        Returns:
            Refund data

        Raises:
            PaymentGatewayError: If refund fails
        """
        if not self._config.enable_refunds:
            raise PaymentGatewayError("Refunds are disabled")

        try:
            refund_data = {}
            if amount is not None:
                refund_data["amount"] = amount

            result = self._sdk.refund().create(payment_id, refund_data)

            if result["status"] not in [200, 201]:
                raise PaymentGatewayError(f"Failed to refund payment: {payment_id}")

            response_data = result["response"]

            return {
                "refund_id": response_data.get("id"),
                "payment_id": response_data.get("payment_id"),
                "amount": response_data.get("amount"),
                "status": response_data.get("status"),
            }

        except Exception as e:
            raise PaymentGatewayError(f"MercadoPago refund error: {str(e)}")
