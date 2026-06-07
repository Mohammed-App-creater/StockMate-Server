from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Database
    DATABASE_URL: str

    # Auth / JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS — origins allowed to call the API from a browser
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8081",
    ]

    # Cloudflare R2 object storage
    CLOUDFLARE_ACCOUNT_ID: str
    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_BUCKET: str
    R2_ENDPOINT: str
    PUBLIC_URL: str

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_db_url(cls, v: str) -> str:
        # Fix scheme — Render/Neon hand out a sync scheme; coerce to asyncpg so
        # the async engine (and async alembic migrations) get a compatible driver.
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)

        # Remove params asyncpg doesn't support (these are libpq/psycopg-only).
        parsed = urlparse(v)
        params = parse_qs(parsed.query)
        params.pop("channel_binding", None)
        params.pop("sslmode", None)

        # Require SSL for remote DBs (Render/Neon); local Postgres has no SSL.
        if parsed.hostname not in ("localhost", "127.0.0.1"):
            params["ssl"] = ["require"]
        else:
            params.pop("ssl", None)

        clean = parsed._replace(query=urlencode(params, doseq=True))
        return urlunparse(clean)


settings = Settings()
