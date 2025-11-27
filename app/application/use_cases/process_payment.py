"""Process payment use case."""
from datetime import datetime

from app.application.interfaces import ICommandUseCase
from app.application.dto import ProcessPaymentDTO, TransactionResponseDTO
from app.domain.interfaces.repositories import ITransactionRepository, IClientRepository
from app.domain.exceptions import EntityNotFoundError, BusinessRuleViolation


class ProcessPaymentUseCase(ICommandUseCase[ProcessPaymentDTO, TransactionResponseDTO]):
    """
    Use case for processing a payment on an existing transaction.

    Marks transaction as paid and updates client balance.
    """

    def __init__(
        self,
        transaction_repository: ITransactionRepository,
        client_repository: IClientRepository,
    ):
        """
        Initialize the use case.

        Args:
            transaction_repository: Transaction repository
            client_repository: Client repository
        """
        self._transaction_repository = transaction_repository
        self._client_repository = client_repository

    async def execute(self, command: ProcessPaymentDTO) -> TransactionResponseDTO:
        """
        Execute the process payment use case.

        Args:
            command: Process payment command DTO

        Returns:
            Updated transaction response DTO

        Raises:
            EntityNotFoundError: If transaction doesn't exist
            BusinessRuleViolation: If payment cannot be processed
        """
        # Get transaction
        transaction = await self._transaction_repository.find_by_id(command.transaction_id)
        if not transaction:
            raise EntityNotFoundError(
                entity_type="Transaction",
                entity_id=str(command.transaction_id)
            )

        # Validate transaction can be paid
        if transaction.is_paid:
            raise BusinessRuleViolation("Transaction is already paid")

        if transaction.is_cancelled:
            raise BusinessRuleViolation("Cannot pay a cancelled transaction")

        # Get client
        client = await self._client_repository.find_by_id(transaction.client_id)
        if not client:
            raise EntityNotFoundError(
                entity_type="Client",
                entity_id=str(transaction.client_id)
            )

        # Mark transaction as paid
        paid_at = command.paid_at or datetime.utcnow()
        transaction.mark_as_paid(
            payment_method=command.payment_method,
            paid_at=paid_at
        )

        # Update transaction
        updated_transaction = await self._transaction_repository.update(
            transaction.id,
            transaction
        )

        # Update client balance if it's an invoice or debit note
        # (payment was already applied when transaction was created,
        # but we mark it as completed)
        # For payment and credit note transactions, apply to balance
        if transaction.transaction_type in ["payment", "credit_note"]:
            client.apply_payment(transaction.total_amount)
            await self._client_repository.update(client.id, client)

        return TransactionResponseDTO.from_entity(updated_transaction)
