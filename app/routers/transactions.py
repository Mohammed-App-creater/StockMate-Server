import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.transaction import TransactionType
from app.models.user import User
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.services import transaction_service

# Prefix ("/transactions") and tags are applied in main.include_router.
router = APIRouter()


@router.post(
    "/",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_transaction(
    tx_in: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransactionResponse:
    return await transaction_service.create_transaction(db, current_user.id, tx_in)


@router.get("/", response_model=list[TransactionResponse])
async def list_transactions(
    type: TransactionType | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TransactionResponse]:
    return await transaction_service.get_transactions(
        db, skip=skip, limit=limit, transaction_type=type
    )


# Declared before "/{transaction_id}" so "product" is not parsed as a UUID.
@router.get(
    "/product/{product_id}",
    response_model=list[TransactionResponse],
)
async def list_transactions_by_product(
    product_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TransactionResponse]:
    return await transaction_service.get_transactions_by_product(
        db, product_id, skip=skip, limit=limit
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransactionResponse:
    return await transaction_service.get_transaction_by_id(db, transaction_id)
