import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.product import ProductUnit


class ProductCreate(BaseModel):
    name: str
    category: str
    unit: ProductUnit
    buying_price: Decimal
    selling_price: Decimal
    barcode: str | None = None
    current_stock: int = 0


class ProductUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    unit: ProductUnit | None = None
    buying_price: Decimal | None = None
    selling_price: Decimal | None = None
    barcode: str | None = None
    current_stock: int | None = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    category: str
    unit: ProductUnit
    buying_price: Decimal
    selling_price: Decimal
    barcode: str | None
    current_stock: int
    created_at: datetime
    updated_at: datetime
