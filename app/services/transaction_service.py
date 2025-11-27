"""
Transaction service for managing billing and payments.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, date
from decimal import Decimal
import uuid

from app.models.transaction import Transaction
from app.models.client import Client


class TransactionService:
    """Service for managing transactions (invoices, payments, etc.)."""

    @staticmethod
    def generate_transaction_number(transaction_type: str) -> str:
        """
        Generate unique transaction number.

        Format: {TYPE}-{TIMESTAMP}-{RANDOM}
        Example: INV-20250118-A3F9
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        random_suffix = uuid.uuid4().hex[:4].upper()
        type_prefix = {
            "invoice": "INV",
            "payment": "PAY",
            "credit_note": "CN",
            "debit_note": "DN",
        }.get(transaction_type, "TXN")

        return f"{type_prefix}-{timestamp}-{random_suffix}"

    @staticmethod
    async def create_transaction(
        db: AsyncSession,
        pharmacy_id: uuid.UUID,
        client_id: uuid.UUID,
        transaction_type: str,
        amount: Decimal,
        tax_amount: Decimal = Decimal("0"),
        discount_amount: Decimal = Decimal("0"),
        **kwargs
    ) -> Transaction:
        """
        Create a new transaction.

        Args:
            db: Database session
            pharmacy_id: Pharmacy UUID
            client_id: Client UUID
            transaction_type: Type (invoice, payment, credit_note, debit_note)
            amount: Base amount
            tax_amount: Tax amount
            discount_amount: Discount amount
            **kwargs: Additional transaction fields

        Returns:
            Transaction: Created transaction object
        """
        # Calculate total
        total_amount = amount + tax_amount - discount_amount

        # Generate transaction number
        transaction_number = TransactionService.generate_transaction_number(transaction_type)

        transaction = Transaction(
            pharmacy_id=pharmacy_id,
            client_id=client_id,
            transaction_number=transaction_number,
            transaction_type=transaction_type,
            amount=amount,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            **kwargs
        )

        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)

        # Update client balance if it's an invoice
        if transaction_type == "invoice":
            from app.services.client_service import ClientService
            await ClientService.update_client_balance(
                db, client_id, pharmacy_id, -float(total_amount)
            )

        return transaction

    @staticmethod
    async def get_transaction(
        db: AsyncSession,
        transaction_id: uuid.UUID,
        pharmacy_id: uuid.UUID
    ) -> Transaction | None:
        """Get transaction by ID (scoped to pharmacy)."""
        result = await db.execute(
            select(Transaction)
            .where(Transaction.id == transaction_id)
            .where(Transaction.pharmacy_id == pharmacy_id)
            .where(Transaction.cancelled_at.is_(None))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_payment_status(
        db: AsyncSession,
        transaction_id: uuid.UUID,
        pharmacy_id: uuid.UUID,
        payment_status: str,
        **updates
    ) -> Transaction | None:
        """
        Update transaction payment status.

        Args:
            db: Database session
            transaction_id: Transaction UUID
            pharmacy_id: Pharmacy UUID
            payment_status: New status
            **updates: Additional fields to update

        Returns:
            Updated Transaction or None
        """
        transaction = await TransactionService.get_transaction(db, transaction_id, pharmacy_id)
        if not transaction:
            return None

        old_status = transaction.payment_status
        transaction.payment_status = payment_status

        # Set paid_at timestamp when completed
        if payment_status == "completed" and not transaction.paid_at:
            transaction.paid_at = datetime.utcnow()

            # Update client balance
            if transaction.transaction_type == "invoice":
                from app.services.client_service import ClientService
                await ClientService.update_client_balance(
                    db, transaction.client_id, pharmacy_id, float(transaction.total_amount)
                )

        # Apply additional updates
        for key, value in updates.items():
            if hasattr(transaction, key):
                setattr(transaction, key, value)

        await db.commit()
        await db.refresh(transaction)

        return transaction

    @staticmethod
    async def list_transactions(
        db: AsyncSession,
        pharmacy_id: uuid.UUID,
        client_id: uuid.UUID | None = None,
        status: str | None = None,
        transaction_type: str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[list[Transaction], int]:
        """List transactions with filtering."""
        query = select(Transaction).where(
            Transaction.pharmacy_id == pharmacy_id,
            Transaction.cancelled_at.is_(None)
        )

        if client_id:
            query = query.where(Transaction.client_id == client_id)
        if status:
            query = query.where(Transaction.payment_status == status)
        if transaction_type:
            query = query.where(Transaction.transaction_type == transaction_type)
        if from_date:
            query = query.where(Transaction.transaction_date >= from_date)
        if to_date:
            query = query.where(Transaction.transaction_date <= to_date)

        # Total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Paginated results
        query = query.order_by(Transaction.transaction_date.desc()).limit(limit).offset(offset)
        result = await db.execute(query)
        transactions = list(result.scalars().all())

        return transactions, (total if total is not None else 0)

    @staticmethod
    async def get_pending_transactions(
        db: AsyncSession,
        pharmacy_id: uuid.UUID,
        client_id: uuid.UUID | None = None
    ) -> list[Transaction]:
        """Get all pending transactions."""
        query = select(Transaction).where(
            Transaction.pharmacy_id == pharmacy_id,
            Transaction.payment_status == "pending",
            Transaction.cancelled_at.is_(None)
        )

        if client_id:
            query = query.where(Transaction.client_id == client_id)

        query = query.order_by(Transaction.due_date.asc().nullsfirst())
        result = await db.execute(query)
        return list(result.scalars().all())
