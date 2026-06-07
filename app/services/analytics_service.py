from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product
from app.models.transaction import ReceiptSplit, Transaction, TransactionType
from app.schemas.analytics import (
    PeriodSummary,
    ProductSummary,
    ReceiptComplianceReport,
)

LOW_STOCK_THRESHOLD = 10
TOP_PRODUCTS_LIMIT = 5

_ZERO = Decimal("0")


def _money(value: Decimal) -> Decimal:
    """Round a monetary/percentage value to 2 decimal places."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


async def _transactions_in_range(
    db: AsyncSession, start_date: datetime, end_date: datetime
) -> list[Transaction]:
    result = await db.execute(
        select(Transaction)
        .where(Transaction.created_at >= start_date)
        .where(Transaction.created_at <= end_date)
        .options(selectinload(Transaction.product))
        .order_by(Transaction.created_at.desc())
    )
    return list(result.scalars().all())


async def get_product_summaries(
    db: AsyncSession, start_date: datetime, end_date: datetime
) -> list[ProductSummary]:
    transactions = await _transactions_in_range(db, start_date, end_date)

    # Aggregate per product id.
    agg: dict = {}
    for tx in transactions:
        bucket = agg.setdefault(
            tx.product_id,
            {
                "name": tx.product.name,
                "total_sold": 0,
                "total_purchased": 0,
                "revenue": _ZERO,
                "cost": _ZERO,
            },
        )
        line = tx.unit_price * tx.total_quantity
        if tx.transaction_type == TransactionType.sale:
            bucket["total_sold"] += tx.total_quantity
            bucket["revenue"] += line - tx.discount_amount
        else:
            bucket["total_purchased"] += tx.total_quantity
            bucket["cost"] += line

    summaries: list[ProductSummary] = []
    for product_id, b in agg.items():
        revenue = b["revenue"]
        cost = b["cost"]
        profit = revenue - cost
        margin = (profit / revenue * 100) if revenue > 0 else _ZERO
        summaries.append(
            ProductSummary(
                product_id=product_id,
                product_name=b["name"],
                total_sold=b["total_sold"],
                total_purchased=b["total_purchased"],
                revenue=_money(revenue),
                cost=_money(cost),
                profit=_money(profit),
                profit_margin_percent=_money(margin),
            )
        )

    summaries.sort(key=lambda s: s.revenue, reverse=True)
    return summaries


async def get_receipt_compliance(
    db: AsyncSession, start_date: datetime, end_date: datetime
) -> ReceiptComplianceReport:
    # Splits joined to their transaction (and product), filtered by date range.
    result = await db.execute(
        select(ReceiptSplit, Transaction)
        .join(Transaction, ReceiptSplit.transaction_id == Transaction.id)
        .where(Transaction.created_at >= start_date)
        .where(Transaction.created_at <= end_date)
        .options(selectinload(Transaction.product))
    )
    rows = result.all()

    purchased_with = 0
    purchased_without = 0
    sold_with = 0
    sold_without = 0

    # Track per-product flags for risky-item detection.
    bought_without: dict = {}  # product_id -> name
    sold_with_names: dict = {}  # product_id -> name

    for split, tx in rows:
        is_sale = tx.transaction_type == TransactionType.sale
        if is_sale:
            if split.has_receipt:
                sold_with += split.quantity
                sold_with_names[tx.product_id] = tx.product.name
            else:
                sold_without += split.quantity
        else:
            if split.has_receipt:
                purchased_with += split.quantity
            else:
                purchased_without += split.quantity
                bought_without[tx.product_id] = tx.product.name

    total_qty = purchased_with + purchased_without + sold_with + sold_without
    if total_qty > 0:
        rate = Decimal(sold_with + purchased_with) / Decimal(total_qty) * 100
    else:
        rate = _ZERO

    # Risky: bought without receipt AND sold with receipt (same product).
    risky_ids = bought_without.keys() & sold_with_names.keys()
    risky_items = sorted(bought_without[pid] for pid in risky_ids)

    # total_transactions = distinct transactions represented by these splits.
    total_transactions = len({tx.id for _, tx in rows})

    return ReceiptComplianceReport(
        total_transactions=total_transactions,
        purchased_with_receipt=purchased_with,
        purchased_without_receipt=purchased_without,
        sold_with_receipt=sold_with,
        sold_without_receipt=sold_without,
        compliance_rate_percent=_money(rate),
        risky_items=risky_items,
    )


async def get_period_summary(
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime,
    period_label: str,
) -> PeriodSummary:
    transactions = await _transactions_in_range(db, start_date, end_date)

    total_revenue = _ZERO
    total_cost = _ZERO
    total_discount = _ZERO
    total_sales = 0
    total_purchases = 0

    for tx in transactions:
        total_discount += tx.discount_amount
        line = tx.unit_price * tx.total_quantity
        if tx.transaction_type == TransactionType.sale:
            total_sales += 1
            total_revenue += line - tx.discount_amount
        else:
            total_purchases += 1
            total_cost += line

    net_profit = total_revenue - total_cost

    summaries = await get_product_summaries(db, start_date, end_date)
    top_products = summaries[:TOP_PRODUCTS_LIMIT]

    low_stock_result = await db.execute(
        select(Product).where(Product.current_stock < LOW_STOCK_THRESHOLD)
    )
    low_stock_products = list(low_stock_result.scalars().all())

    receipt_compliance = await get_receipt_compliance(db, start_date, end_date)

    return PeriodSummary(
        period=period_label,
        total_revenue=_money(total_revenue),
        total_cost=_money(total_cost),
        net_profit=_money(net_profit),
        total_discount=_money(total_discount),
        total_transactions=len(transactions),
        total_sales=total_sales,
        total_purchases=total_purchases,
        top_products=top_products,
        low_stock_products=low_stock_products,
        receipt_compliance=receipt_compliance,
    )
