"""Client API endpoints using Clean Architecture."""
from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from decimal import Decimal

from app.application.dto import CreateClientDTO, ClientResponseDTO
from app.infrastructure.dependencies.use_cases import CreateClientUseCaseDep, GetClientUseCaseDep
from app.domain.exceptions import DuplicateEntityError, EntityNotFoundError, ValidationError


router = APIRouter(prefix="/clients", tags=["clients"])


# Pydantic schemas for API validation
class CreateClientRequest(BaseModel):
    """Request schema for creating a client."""

    pharmacy_id: UUID
    phone: str = Field(..., description="Phone number")
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    tax_id: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str = "AR"
    credit_limit: Decimal = Field(default=Decimal("0"), description="Credit limit in ARS")
    whatsapp_opted_in: bool = True
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None


class ClientResponse(BaseModel):
    """Response schema for client."""

    id: UUID
    pharmacy_id: UUID
    phone: str
    phone_normalized: str
    first_name: str | None
    last_name: str | None
    full_name: str | None
    email: str | None
    tax_id: str | None
    address: str | None
    city: str | None
    state: str | None
    postal_code: str | None
    country: str
    credit_limit: Decimal
    current_balance: Decimal
    available_credit: Decimal
    owes_money: bool
    status: str
    whatsapp_opted_in: bool
    tags: list[str]

    class Config:
        from_attributes = True


@router.post(
    "/",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new client",
    description="Creates a new client for a pharmacy with automatic phone normalization and validation"
)
async def create_client(
    request: CreateClientRequest,
    use_case: CreateClientUseCaseDep
) -> ClientResponse:
    """
    Create a new client.

    This endpoint uses Clean Architecture:
    - Request → DTO → Use Case → Domain Logic → Repository → Response

    Args:
        request: Client creation request
        use_case: Injected CreateClientUseCase

    Returns:
        Created client data

    Raises:
        400: Validation error or duplicate phone number
        500: Internal server error
    """
    try:
        # Convert API request to application DTO
        command = CreateClientDTO(
            pharmacy_id=request.pharmacy_id,
            phone=request.phone,
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email,
            tax_id=request.tax_id,
            address=request.address,
            city=request.city,
            state=request.state,
            postal_code=request.postal_code,
            country=request.country,
            credit_limit=request.credit_limit,
            whatsapp_opted_in=request.whatsapp_opted_in,
            tags=request.tags,
            notes=request.notes,
        )

        # Execute use case
        result = await use_case.execute(command)

        # Convert DTO to API response
        return ClientResponse(
            id=result.id,
            pharmacy_id=result.pharmacy_id,
            phone=result.phone,
            phone_normalized=result.phone_normalized,
            first_name=result.first_name,
            last_name=result.last_name,
            full_name=result.full_name,
            email=result.email,
            tax_id=result.tax_id,
            address=result.address,
            city=result.city,
            state=result.state,
            postal_code=result.postal_code,
            country=result.country,
            credit_limit=result.credit_limit,
            current_balance=result.current_balance,
            available_credit=result.available_credit,
            owes_money=result.owes_money,
            status=result.status,
            whatsapp_opted_in=result.whatsapp_opted_in,
            tags=result.tags,
        )

    except DuplicateEntityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/{client_id}",
    response_model=ClientResponse,
    summary="Get client by ID",
    description="Retrieves a client by their unique identifier"
)
async def get_client(
    client_id: UUID,
    use_case: GetClientUseCaseDep
) -> ClientResponse:
    """
    Get a client by ID.

    Args:
        client_id: Client unique identifier
        use_case: Injected GetClientUseCase

    Returns:
        Client data

    Raises:
        404: Client not found
        500: Internal server error
    """
    try:
        # Execute query use case
        result = await use_case.execute(client_id)

        # Convert DTO to API response
        return ClientResponse(
            id=result.id,
            pharmacy_id=result.pharmacy_id,
            phone=result.phone,
            phone_normalized=result.phone_normalized,
            first_name=result.first_name,
            last_name=result.last_name,
            full_name=result.full_name,
            email=result.email,
            tax_id=result.tax_id,
            address=result.address,
            city=result.city,
            state=result.state,
            postal_code=result.postal_code,
            country=result.country,
            credit_limit=result.credit_limit,
            current_balance=result.current_balance,
            available_credit=result.available_credit,
            owes_money=result.owes_money,
            status=result.status,
            whatsapp_opted_in=result.whatsapp_opted_in,
            tags=result.tags,
        )

    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
