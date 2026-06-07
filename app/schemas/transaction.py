import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.transaction import TransactionType
from app.schemas.product import ProductResponse


class ReceiptSplitCreate(BaseModel):
    quantity: int = Field(gt=0)
    has_receipt: bool


class ReceiptSplitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    quantity: int
    has_receipt: bool


class TransactionCreate(BaseModel):
    product_id: uuid.UUID
    transaction_type: TransactionType
    total_quantity: int = Field(gt=0)
    unit_price: Decimal
    discount_amount: Decimal = Decimal("0")
    notes: str | None = None
    receipt_splits: list[ReceiptSplitCreate]

    @model_validator(mode="after")
    def _validate_splits(self) -> "TransactionCreate":
        if not self.receipt_splits:
            raise ValueError("Receipt splits must sum to total_quantity")
        if sum(s.quantity for s in self.receipt_splits) != self.total_quantity:
            raise ValueError("Receipt splits must sum to total_quantity")
        return self


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    transaction_type: TransactionType
    total_quantity: int
    unit_price: Decimal
    discount_amount: Decimal
    notes: str | None
    created_at: datetime
    receipt_splits: list[ReceiptSplitResponse]
    product: ProductResponse
