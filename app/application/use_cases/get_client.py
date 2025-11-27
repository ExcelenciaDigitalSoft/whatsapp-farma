"""Get client use case."""
from uuid import UUID

from app.application.interfaces import IQueryUseCase
from app.application.dto import ClientResponseDTO
from app.domain.interfaces.repositories import IClientRepository
from app.domain.exceptions import EntityNotFoundError


class GetClientUseCase(IQueryUseCase[UUID, ClientResponseDTO]):
    """
    Use case for retrieving a client by ID.

    Query-side operation following CQRS pattern.
    """

    def __init__(self, client_repository: IClientRepository):
        """
        Initialize the use case.

        Args:
            client_repository: Client repository implementation
        """
        self._client_repository = client_repository

    async def execute(self, query: UUID) -> ClientResponseDTO:
        """
        Execute the get client query.

        Args:
            query: Client ID to retrieve

        Returns:
            Client response DTO

        Raises:
            EntityNotFoundError: If client doesn't exist
        """
        client = await self._client_repository.find_by_id(query)

        if not client:
            raise EntityNotFoundError(
                entity_type="Client",
                entity_id=str(query)
            )

        return ClientResponseDTO.from_entity(client)
