# StockMate API

Wholesale inventory and accounting API — auth, products, transactions, and analytics.

## Local Development
1. Clone repo
2. Copy `.env.example` → `.env` and fill values
3. `docker compose up db -d`
4. `alembic upgrade head`
5. `uvicorn app.main:app --reload`

Create the first admin user (optional):

```
python scripts/create_admin.py
```

## Deploy to Railway
1. Push to GitHub
2. Connect repo to Railway
3. Add environment variables from `.env.example`
4. Railway auto-deploys on push

## API Docs
http://localhost:8000/docs
