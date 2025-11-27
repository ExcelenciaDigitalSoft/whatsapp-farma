"""Create transaction use case."""
from app.application.interfaces import ICommandUseCase
from app.application.dto import CreateTransactionDTO, TransactionResponseDTO
from app.domain.interfaces.repositories import ITransactionRepository, IClientRepository
from app.domain.entities import Transaction, TransactionItem
from app.domain.value_objects import Money
from app.domain.services import TransactionNumberGenerator, ClientValidator
from app.domain.exceptions import EntityNotFoundError, ValidationError


class CreateTransactionUseCase(ICommandUseCase[CreateTransactionDTO, TransactionResponseDTO]):
    """
    Use case for creating a new transaction.

    Handles transaction creation with business rule validation,
    automatic number generation, and client balance updates.
    """

    def __init__(
        self,
        transaction_repository: ITransactionRepository,
        client_repository: IClientRepository,
        transaction_number_generator: TransactionNumberGenerator,
        client_validator: ClientValidator,
    ):
        """
        Initialize the use case.

        Args:
            transaction_repository: Transaction repository
            client_repository: Client repository
            transaction_number_generator: Transaction number generator service
            client_validator: Client validator service
        """
        self._transaction_repository = transaction_repository
        self._client_repository = client_repository
        self._number_generator = transaction_number_generator
        self._client_validator = client_validator

    async def execute(self, command: CreateTransactionDTO) -> TransactionResponseDTO:
        """
        Execute the create transaction use case.

        Args:
            command: Create transaction command DTO

        Returns:
            Created transaction response DTO

        Raises:
            EntityNotFoundError: If client doesn't exist
            ValidationError: If input validation fails
            BusinessRuleViolation: If business rules are violated
        """
        # Validate client exists
        client = await self._client_repository.find_by_id(command.client_id)
        if not client:
            raise EntityNotFoundError(
                entity_type="Client",
                entity_id=str(command.client_id)
            )

        # Create money value objects
        amount = Money.create(command.amount, command.currency)
        tax_amount = Money.create(command.tax_amount, command.currency)
        discount_amount = Money.create(command.discount_amount, command.currency)

        # Calculate total
        total_amount = amount + tax_amount - discount_amount

        # For invoices and debit notes, validate client can make purchase
        if command.transaction_type in ["invoice", "debit_note"]:
            self._client_validator.validate_for_transaction(client, total_amount)

        # Ensure transaction_date is set (should be set in DTO __post_init__)
        transaction_date = command.transaction_date
        if transaction_date is None:
            from datetime import date
            transaction_date = date.today()

        # Generate transaction number
        sequence = await self._transaction_repository.get_next_sequence_number(
            pharmacy_id=command.pharmacy_id,
            transaction_type=command.transaction_type,
            transaction_date=transaction_date
        )

        transaction_number = self._number_generator.generate(
            transaction_type=command.transaction_type,
            sequence=sequence,
            transaction_date=transaction_date
        )

        # Create transaction entity
        transaction = Transaction(
            pharmacy_id=command.pharmacy_id,
            client_id=command.client_id,
            transaction_number=transaction_number,
            transaction_type=command.transaction_type,
            amount=amount,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            payment_method=command.payment_method,
            description=command.description,
            transaction_date=transaction_date,
            due_date=command.due_date,
            extra_metadata=command.extra_metadata or {},
        )

        # Add items if provided
        if command.items:
            for item_dto in command.items:
                unit_price = Money.create(item_dto.unit_price, command.currency)
                total = Money.create(item_dto.total, command.currency)

                item = TransactionItem(
                    name=item_dto.name,
                    quantity=item_dto.quantity,
                    unit_price=unit_price,
                    total=total
                )
                transaction.add_item(item)

        # Save transaction
        saved_transaction = await self._transaction_repository.create(transaction)

        # Update client balance for invoices and debit notes
        if command.transaction_type in ["invoice", "debit_note"]:
            client.apply_charge(total_amount, description=command.description)
            await self._client_repository.update(client.id, client)

        # Update client balance for payments and credit notes
        elif command.transaction_type in ["payment", "credit_note"]:
            client.apply_payment(total_amount)
            await self._client_repository.update(client.id, client)

        return TransactionResponseDTO.from_entity(saved_transaction)
