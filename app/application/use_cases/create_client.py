"""Create client use case."""
from app.application.interfaces import ICommandUseCase
from app.application.dto import CreateClientDTO, ClientResponseDTO
from app.domain.interfaces.repositories import IClientRepository
from app.domain.entities import Client
from app.domain.value_objects import Phone, Email, Address, TaxId, Money, ClientBalance
from app.domain.exceptions import DuplicateEntityError, ValidationError


class CreateClientUseCase(ICommandUseCase[CreateClientDTO, ClientResponseDTO]):
    """
    Use case for creating a new client.

    Validates business rules and ensures no duplicate clients exist
    for the same phone number within a pharmacy.
    """

    def __init__(self, client_repository: IClientRepository):
        """
        Initialize the use case.

        Args:
            client_repository: Client repository implementation
        """
        self._client_repository = client_repository

    async def execute(self, command: CreateClientDTO) -> ClientResponseDTO:
        """
        Execute the create client use case.

        Args:
            command: Create client command DTO

        Returns:
            Created client response DTO

        Raises:
            DuplicateEntityError: If client with same phone already exists
            ValidationError: If input validation fails
        """
        # Create phone value object
        phone = Phone.create(command.phone)

        # Check for duplicate phone number in pharmacy
        existing = await self._client_repository.find_by_phone(
            phone=phone,
            pharmacy_id=command.pharmacy_id
        )

        if existing:
            raise DuplicateEntityError(
                entity_type="Client",
                field="phone",
                value=str(phone)
            )

        # Create email value object if provided
        email = None
        if command.email:
            email = Email.create(command.email)

        # Create tax ID value object if provided
        tax_id = None
        if command.tax_id:
            tax_id = TaxId.create(command.tax_id)

        # Create address value object
        address = Address.create(
            street=command.address,
            city=command.city,
            state=command.state,
            postal_code=command.postal_code,
            country=command.country
        )

        # Create client balance
        credit_limit = Money.create(command.credit_limit, "ARS")
        balance = ClientBalance.create(
            current_balance=Money.zero("ARS"),
            credit_limit=credit_limit
        )

        # Create client entity
        client = Client(
            pharmacy_id=command.pharmacy_id,
            phone=phone,
            balance=balance,
            first_name=command.first_name,
            last_name=command.last_name,
            email=email,
            tax_id=tax_id,
            address=address,
            whatsapp_opted_in=command.whatsapp_opted_in,
            tags=command.tags or [],
            notes=command.notes,
            external_id=command.external_id,
        )

        # Save to repository
        saved_client = await self._client_repository.create(client)

        # Return response DTO
        return ClientResponseDTO.from_entity(saved_client)
