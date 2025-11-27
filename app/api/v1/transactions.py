"""
Transaction API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
import uuid

from app.db.session import get_db
from app.middleware.auth_middleware import get_current_pharmacy_id
from app.services.transaction_service import TransactionService
from app.schemas.transaction_schema import TransactionCreate, TransactionResponse, TransactionListResponse

router = APIRouter()


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    pharmacy_id: uuid.UUID = Depends(get_current_pharmacy_id)
):
    """Create a new transaction (invoice, payment, etc.)."""
    transaction = await TransactionService.create_transaction(
        db,
        pharmacy_id=pharmacy_id,
        **transaction_data.model_dump()
    )
    return transaction


@router.get("/", response_model=TransactionListResponse)
async def list_transactions(
    client_id: uuid.UUID | None = None,
    status_filter: str | None = Query(None, alias="status"),
    transaction_type: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    pharmacy_id: uuid.UUID = Depends(get_current_pharmacy_id)
):
    """List transactions with optional filtering."""
    transactions, total = await TransactionService.list_transactions(
        db,
        pharmacy_id=pharmacy_id,
        client_id=client_id,
        status=status_filter,
        transaction_type=transaction_type,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        offset=offset
    )
    return {
        "data": transactions,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    pharmacy_id: uuid.UUID = Depends(get_current_pharmacy_id)
):
    """Get transaction by ID."""
    transaction = await TransactionService.get_transaction(db, transaction_id, pharmacy_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    return transaction


@router.get("/pending/all", response_model=list[TransactionResponse])
async def get_pending_transactions(
    client_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    pharmacy_id: uuid.UUID = Depends(get_current_pharmacy_id)
):
    """Get all pending transactions."""
    transactions = await TransactionService.get_pending_transactions(
        db, pharmacy_id, client_id
    )
    return transactions
