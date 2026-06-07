from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import analytics, auth, products, transactions

app = FastAPI(
    title="StockMate API",
    description="Wholesale inventory and accounting API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# The auth router already declares prefix="/auth", so include it without an
# additional prefix to avoid producing "/auth/auth/...".
app.include_router(auth.router)
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(
    transactions.router, prefix="/transactions", tags=["transactions"]
)
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])


@app.get("/")
async def health_check() -> dict[str, str]:
    return {"status": "StockMate API running", "version": "0.1.0"}
