"""
Payment service for Mercado Pago integration.
"""
import mercadopago
import uuid

from app.core.config import settings
from app.models.transaction import Transaction


class PaymentService:
    """Service for Mercado Pago payment integration."""

    def __init__(self):
        """Initialize Mercado Pago SDK."""
        self.sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN) if settings.MERCADOPAGO_ACCESS_TOKEN else None

    def create_payment_preference(
        self,
        transaction: Transaction,
        client_email: str | None = None,
        back_url: str | None = None
    ) -> dict:
        """
        Create Mercado Pago payment preference.

        Args:
            transaction: Transaction object
            client_email: Client email (optional)
            back_url: URL to redirect after payment (optional)

        Returns:
            dict: Mercado Pago response with preference ID and init_point (payment link)
        """
        if not self.sdk:
            raise ValueError("Mercado Pago not configured")

        # Prepare items
        items = []
        if transaction.items:
            for item in transaction.items:
                items.append({
                    "title": item.get("name", "Item"),
                    "quantity": item.get("quantity", 1),
                    "unit_price": float(item.get("unit_price", 0)),
                    "currency_id": transaction.currency,
                })
        else:
            # Single item with transaction total
            items.append({
                "title": f"Factura {transaction.transaction_number}",
                "quantity": 1,
                "unit_price": float(transaction.total_amount),
                "currency_id": transaction.currency,
            })

        # Prepare preference data
        preference_data = {
            "items": items,
            "external_reference": str(transaction.id),
            "statement_descriptor": "Farmacia",
            "notification_url": f"{back_url}/api/v1/payments/webhook" if back_url else None,
            "back_urls": {
                "success": f"{back_url}/payment/success" if back_url else None,
                "failure": f"{back_url}/payment/failure" if back_url else None,
                "pending": f"{back_url}/payment/pending" if back_url else None,
            },
            "auto_return": "approved",
        }

        if client_email:
            preference_data["payer"] = {"email": client_email}

        # Create preference
        response = self.sdk.preference().create(preference_data)

        if response["status"] == 200 or response["status"] == 201:
            return {
                "preference_id": response["response"]["id"],
                "init_point": response["response"]["init_point"],  # Desktop payment link
                "sandbox_init_point": response["response"].get("sandbox_init_point"),  # Sandbox link
                "qr_code": response["response"].get("qr_code"),
            }
        else:
            raise Exception(f"Mercado Pago error: {response}")

    def get_payment_info(self, payment_id: str) -> dict:
        """
        Get payment information from Mercado Pago.

        Args:
            payment_id: Mercado Pago payment ID

        Returns:
            dict: Payment information
        """
        if not self.sdk:
            raise ValueError("Mercado Pago not configured")

        response = self.sdk.payment().get(payment_id)

        if response["status"] == 200:
            return response["response"]
        else:
            raise Exception(f"Mercado Pago error: {response}")

    @staticmethod
    def validate_webhook_signature(request_data: dict, headers: dict) -> bool:
        """
        Validate Mercado Pago webhook signature.

        Args:
            request_data: Webhook payload
            headers: Request headers

        Returns:
            bool: True if signature is valid
        """
        # TODO: Implement proper signature validation
        # For now, just check if it's a valid Mercado Pago event
        return "type" in request_data and "data" in request_data
