"""
Client API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.db.session import get_db
from app.middleware.auth_middleware import get_current_pharmacy_id
from app.services.client_service import ClientService
from app.schemas.client_schema import ClientCreate, ClientUpdate, ClientResponse, ClientListResponse

router = APIRouter()


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    db: AsyncSession = Depends(get_db),
    pharmacy_id: uuid.UUID = Depends(get_current_pharmacy_id)
):
    """Create a new client."""
    # Check if client with same phone already exists
    existing_client = await ClientService.get_client_by_phone(
        db, client_data.phone, pharmacy_id
    )
    if existing_client:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Client with this phone number already exists"
        )

    client = await ClientService.create_client(
        db,
        pharmacy_id=pharmacy_id,
        **client_data.model_dump()
    )
    return client


@router.get("/", response_model=ClientListResponse)
async def list_clients(
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    pharmacy_id: uuid.UUID = Depends(get_current_pharmacy_id)
):
    """List all clients for the pharmacy."""
    clients, total = await ClientService.list_clients(
        db,
        pharmacy_id=pharmacy_id,
        status=status_filter,
        search=search,
        limit=limit,
        offset=offset
    )
    return {
        "data": clients,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    pharmacy_id: uuid.UUID = Depends(get_current_pharmacy_id)
):
    """Get client by ID."""
    client = await ClientService.get_client(db, client_id, pharmacy_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    return client


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: uuid.UUID,
    client_data: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    pharmacy_id: uuid.UUID = Depends(get_current_pharmacy_id)
):
    """Update client information."""
    # Filter out None values
    updates = {k: v for k, v in client_data.model_dump().items() if v is not None}

    client = await ClientService.update_client(
        db, client_id, pharmacy_id, **updates
    )
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    pharmacy_id: uuid.UUID = Depends(get_current_pharmacy_id)
):
    """Soft delete a client."""
    deleted = await ClientService.delete_client(db, client_id, pharmacy_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )


@router.get("/by-phone/{phone}", response_model=ClientResponse)
async def get_client_by_phone(
    phone: str,
    db: AsyncSession = Depends(get_db),
    pharmacy_id: uuid.UUID = Depends(get_current_pharmacy_id)
):
    """Get client by phone number."""
    client = await ClientService.get_client_by_phone(db, phone, pharmacy_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    return client
