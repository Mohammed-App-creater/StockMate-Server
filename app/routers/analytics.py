from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.analytics import (
    PeriodSummary,
    ProductSummary,
    ReceiptComplianceReport,
)
from app.services import analytics_service

# Prefix ("/analytics") and tags are applied in main.include_router.
router = APIRouter()


def _utcnow() -> datetime:
    # created_at is a timestamptz column, so range bounds must be tz-aware UTC;
    # a naive datetime.utcnow() compares as a different type and matches nothing.
    return datetime.now(timezone.utc)


def _as_utc(value: datetime | None) -> datetime | None:
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


@router.get("/summary/daily", response_model=PeriodSummary)
async def daily_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PeriodSummary:
    now = _utcnow()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return await analytics_service.get_period_summary(db, start, now, "daily")


@router.get("/summary/weekly", response_model=PeriodSummary)
async def weekly_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PeriodSummary:
    now = _utcnow()
    return await analytics_service.get_period_summary(
        db, now - timedelta(days=7), now, "weekly"
    )


@router.get("/summary/monthly", response_model=PeriodSummary)
async def monthly_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PeriodSummary:
    now = _utcnow()
    return await analytics_service.get_period_summary(
        db, now - timedelta(days=30), now, "monthly"
    )


@router.get("/summary/yearly", response_model=PeriodSummary)
async def yearly_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PeriodSummary:
    now = _utcnow()
    return await analytics_service.get_period_summary(
        db, now - timedelta(days=365), now, "yearly"
    )


@router.get("/compliance", response_model=ReceiptComplianceReport)
async def compliance_report(
    start: datetime | None = None,
    end: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReceiptComplianceReport:
    end = _as_utc(end) or _utcnow()
    start = _as_utc(start) or (end - timedelta(days=30))
    return await analytics_service.get_receipt_compliance(db, start, end)


@router.get("/products", response_model=list[ProductSummary])
async def product_summaries(
    start: datetime | None = None,
    end: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProductSummary]:
    end = _as_utc(end) or _utcnow()
    start = _as_utc(start) or (end - timedelta(days=30))
    return await analytics_service.get_product_summaries(db, start, end)
