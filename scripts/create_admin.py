"""Create the initial admin user.

Usage:
    python scripts/create_admin.py

Reads ADMIN_USERNAME, ADMIN_PASSWORD and ADMIN_FULL_NAME from the environment,
prompting interactively for any that are missing. Inserts the user directly via
SQLAlchemy and is a no-op if the username already exists.
"""

import asyncio
import os
import sys
from getpass import getpass
from pathlib import Path

# Allow running as a standalone script (python scripts/create_admin.py).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.database import AsyncSessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402


def _resolve(env_key: str, prompt: str, *, secret: bool = False) -> str:
    value = os.getenv(env_key)
    if value:
        return value
    value = getpass(prompt) if secret else input(prompt)
    value = value.strip()
    if not value:
        print(f"{env_key} is required.")
        sys.exit(1)
    return value


async def create_admin() -> None:
    username = _resolve("ADMIN_USERNAME", "Admin username: ")
    full_name = _resolve("ADMIN_FULL_NAME", "Admin full name: ")
    password = _resolve("ADMIN_PASSWORD", "Admin password: ", secret=True)

    async with AsyncSessionLocal() as db:
        existing = await db.execute(
            select(User).where(User.username == username)
        )
        if existing.scalar_one_or_none() is not None:
            print("User already exists")
            return

        user = User(
            username=username,
            full_name=full_name,
            hashed_password=hash_password(password),
        )
        db.add(user)
        await db.commit()
        print("User created")


if __name__ == "__main__":
    asyncio.run(create_admin())
