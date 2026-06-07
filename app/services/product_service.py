import uuid

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


async def get_product_by_barcode(db: AsyncSession, barcode: str) -> Product:
    result = await db.execute(select(Product).where(Product.barcode == barcode))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product


async def get_product_by_id(db: AsyncSession, product_id: uuid.UUID) -> Product:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product


async def create_product(db: AsyncSession, product_in: ProductCreate) -> Product:
    if product_in.barcode is not None:
        result = await db.execute(
            select(Product).where(Product.barcode == product_in.barcode)
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Barcode already registered",
            )

    product = Product(**product_in.model_dump())
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return product


async def get_all_products(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> list[Product]:
    result = await db.execute(
        select(Product)
        .order_by(Product.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def update_product(
    db: AsyncSession, product_id: uuid.UUID, product_in: ProductUpdate
) -> Product:
    product = await get_product_by_id(db, product_id)

    updates = product_in.model_dump(exclude_unset=True)
    for field, value in updates.items():
        if value is not None:
            setattr(product, field, value)

    await db.flush()
    await db.refresh(product)
    return product


async def delete_product(db: AsyncSession, product_id: uuid.UUID) -> dict[str, str]:
    product = await get_product_by_id(db, product_id)
    await db.delete(product)
    await db.flush()
    return {"message": "Product deleted"}


async def search_products(db: AsyncSession, query: str) -> list[Product]:
    pattern = f"%{query}%"
    result = await db.execute(
        select(Product)
        .where(
            or_(
                Product.name.ilike(pattern),
                Product.category.ilike(pattern),
            )
        )
        .order_by(Product.created_at.desc())
    )
    return list(result.scalars().all())
