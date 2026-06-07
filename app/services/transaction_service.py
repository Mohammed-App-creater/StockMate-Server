import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product
from app.models.transaction import ReceiptSplit, Transaction, TransactionType
from app.schemas.transaction import TransactionCreate

# Eager-load splits and product so responses serialize without lazy I/O on an
# async session (lazy loads would raise outside the awaited query context).
_EAGER = (
    selectinload(Transaction.receipt_splits),
    selectinload(Transaction.product),
)


async def _get_loaded(
    db: AsyncSession, transaction_id: uuid.UUID
) -> Transaction | None:
    result = await db.execute(
        select(Transaction)
        .where(Transaction.id == transaction_id)
        .options(*_EAGER)
    )
    return result.scalar_one_or_none()


async def create_transaction(
    db: AsyncSession, user_id: uuid.UUID, tx_in: TransactionCreate
) -> Transaction:
    result = await db.execute(
        select(Product).where(Product.id == tx_in.product_id)
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    if tx_in.transaction_type == TransactionType.sale:
        if product.current_stock < tx_in.total_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient stock",
            )

    transaction = Transaction(
        user_id=user_id,
        product_id=tx_in.product_id,
        transaction_type=tx_in.transaction_type,
        total_quantity=tx_in.total_quantity,
        unit_price=tx_in.unit_price,
        discount_amount=tx_in.discount_amount,
        notes=tx_in.notes,
    )
    transaction.receipt_splits = [
        ReceiptSplit(quantity=split.quantity, has_receipt=split.has_receipt)
        for split in tx_in.receipt_splits
    ]
    db.add(transaction)

    if tx_in.transaction_type == TransactionType.purchase:
        product.current_stock += tx_in.total_quantity
    else:
        product.current_stock -= tx_in.total_quantity

    await db.flush()
    # Re-fetch with relationships eagerly loaded for the response.
    loaded = await _get_loaded(db, transaction.id)
    assert loaded is not None
    return loaded


async def get_transaction_by_id(
    db: AsyncSession, transaction_id: uuid.UUID
) -> Transaction:
    transaction = await _get_loaded(db, transaction_id)
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return transaction


async def get_transactions(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    transaction_type: TransactionType | None = None,
) -> list[Transaction]:
    stmt = select(Transaction).options(*_EAGER)
    if transaction_type is not None:
        stmt = stmt.where(Transaction.transaction_type == transaction_type)
    stmt = stmt.order_by(Transaction.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_transactions_by_product(
    db: AsyncSession,
    product_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> list[Transaction]:
    result = await db.execute(
        select(Transaction)
        .where(Transaction.product_id == product_id)
        .options(*_EAGER)
        .order_by(Transaction.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())
