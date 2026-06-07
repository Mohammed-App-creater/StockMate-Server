import uuid
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.product import ProductResponse


class ProductSummary(BaseModel):
    product_id: uuid.UUID
    product_name: str
    total_sold: int
    total_purchased: int
    revenue: Decimal
    cost: Decimal
    profit: Decimal
    profit_margin_percent: Decimal


class ReceiptComplianceReport(BaseModel):
    total_transactions: int
    purchased_with_receipt: int
    purchased_without_receipt: int
    sold_with_receipt: int
    sold_without_receipt: int
    compliance_rate_percent: Decimal
    risky_items: list[str]


class PeriodSummary(BaseModel):
    period: str
    total_revenue: Decimal
    total_cost: Decimal
    net_profit: Decimal
    total_discount: Decimal
    total_transactions: int
    total_sales: int
    total_purchases: int
    top_products: list[ProductSummary]
    low_stock_products: list[ProductResponse]
    receipt_compliance: ReceiptComplianceReport
