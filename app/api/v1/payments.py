"""
Payment API endpoints (Mercado Pago integration).
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.db.session import get_db
from app.middleware.auth_middleware import get_current_pharmacy_id
from app.services.transaction_service import TransactionService
from app.services.payment_service import PaymentService

router = APIRouter()


@router.post("/{transaction_id}/create-link")
async def create_payment_link(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    pharmacy_id: uuid.UUID = Depends(get_current_pharmacy_id)
):
    """
    Create Mercado Pago payment link for a transaction.

    Returns payment link (init_point) and preference ID.
    """
    # Get transaction
    transaction = await TransactionService.get_transaction(db, transaction_id, pharmacy_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    # Check if already has payment link
    if transaction.mercadopago_preference_id:
        return {
            "transaction_id": str(transaction.id),
            "payment_link": transaction.mercadopago_payment_link,
            "preference_id": transaction.mercadopago_preference_id,
            "already_created": True
        }

    # Create payment preference
    payment_service = PaymentService()
    try:
        result = payment_service.create_payment_preference(transaction)

        # Update transaction with payment info
        await TransactionService.update_payment_status(
            db,
            transaction_id,
            pharmacy_id,
            payment_status="pending",
            mercadopago_preference_id=result["preference_id"],
            mercadopago_payment_link=result["init_point"]
        )

        return {
            "transaction_id": str(transaction.id),
            "payment_link": result["init_point"],
            "preference_id": result["preference_id"],
            "qr_code": result.get("qr_code"),
            "already_created": False
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment link: {str(e)}"
        )


@router.post("/webhook")
async def mercadopago_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Mercado Pago webhook endpoint for payment notifications.

    This endpoint is called by Mercado Pago when payment status changes.
    """
    try:
        data = await request.json()

        # Validate webhook signature
        if not PaymentService.validate_webhook_signature(data, dict(request.headers)):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )

        # Handle payment notification
        if data.get("type") == "payment":
            payment_id = data.get("data", {}).get("id")

            if payment_id:
                # Get payment info from Mercado Pago
                payment_service = PaymentService()
                payment_info = payment_service.get_payment_info(payment_id)

                # Get transaction by external_reference
                external_reference = payment_info.get("external_reference")
                if external_reference:
                    transaction_id = uuid.UUID(external_reference)

                    # Update transaction status based on payment status
                    status_mapping = {
                        "approved": "completed",
                        "pending": "pending",
                        "in_process": "pending",
                        "rejected": "failed",
                        "cancelled": "cancelled",
                        "refunded": "refunded",
                    }

                    mp_status = payment_info.get("status")
                    new_status = status_mapping.get(mp_status if mp_status else "", "pending")

                    # Find pharmacy_id from transaction
                    from sqlalchemy import select
                    from app.models.transaction import Transaction

                    result = await db.execute(
                        select(Transaction).where(Transaction.id == transaction_id)
                    )
                    transaction = result.scalar_one_or_none()

                    if transaction:
                        await TransactionService.update_payment_status(
                            db,
                            transaction_id,
                            transaction.pharmacy_id,
                            payment_status=new_status,
                            mercadopago_payment_id=payment_id
                        )

        return {"status": "ok"}

    except Exception as e:
        # Log error but return 200 to avoid Mercado Pago retries
        print(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}
