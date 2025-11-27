"""Use case dependency providers for FastAPI."""
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases import (
    CreateClientUseCase,
    GetClientUseCase,
    CreateTransactionUseCase,
    ProcessPaymentUseCase,
)
from app.infrastructure.database.repositories import ClientRepository
from app.domain.services import TransactionNumberGenerator, ClientValidator
from app.infrastructure.dependencies.database import get_db


# Client Use Cases

def get_create_client_use_case(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> CreateClientUseCase:
    """
    Provide CreateClientUseCase with dependencies.

    Args:
        db: Database session

    Returns:
        CreateClientUseCase instance
    """
    client_repository = ClientRepository(db)
    return CreateClientUseCase(client_repository=client_repository)


def get_get_client_use_case(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> GetClientUseCase:
    """
    Provide GetClientUseCase with dependencies.

    Args:
        db: Database session

    Returns:
        GetClientUseCase instance
    """
    client_repository = ClientRepository(db)
    return GetClientUseCase(client_repository=client_repository)


# Transaction Use Cases

def get_create_transaction_use_case(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> CreateTransactionUseCase:
    """
    Provide CreateTransactionUseCase with dependencies.

    Args:
        db: Database session

    Returns:
        CreateTransactionUseCase instance
    """
    # Note: TransactionRepository not yet implemented, this is a placeholder
    # Once implemented, replace with actual repository
    from app.infrastructure.database.repositories import ClientRepository

    client_repository = ClientRepository(db)
    # transaction_repository = TransactionRepository(db)  # TODO: Implement
    transaction_repository = None  # type: ignore[assignment]  # Placeholder until TransactionRepository is implemented

    transaction_number_generator = TransactionNumberGenerator()
    client_validator = ClientValidator()

    return CreateTransactionUseCase(
        transaction_repository=transaction_repository,  # type: ignore[arg-type]
        client_repository=client_repository,
        transaction_number_generator=transaction_number_generator,
        client_validator=client_validator,
    )


def get_process_payment_use_case(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ProcessPaymentUseCase:
    """
    Provide ProcessPaymentUseCase with dependencies.

    Args:
        db: Database session

    Returns:
        ProcessPaymentUseCase instance
    """
    # Note: TransactionRepository not yet implemented
    client_repository = ClientRepository(db)
    # transaction_repository = TransactionRepository(db)  # TODO: Implement
    transaction_repository = None  # type: ignore[assignment]  # Placeholder until TransactionRepository is implemented

    return ProcessPaymentUseCase(
        transaction_repository=transaction_repository,  # type: ignore[arg-type]
        client_repository=client_repository,
    )


# Type aliases for cleaner endpoint signatures
CreateClientUseCaseDep = Annotated[CreateClientUseCase, Depends(get_create_client_use_case)]
GetClientUseCaseDep = Annotated[GetClientUseCase, Depends(get_get_client_use_case)]
CreateTransactionUseCaseDep = Annotated[CreateTransactionUseCase, Depends(get_create_transaction_use_case)]
ProcessPaymentUseCaseDep = Annotated[ProcessPaymentUseCase, Depends(get_process_payment_use_case)]
