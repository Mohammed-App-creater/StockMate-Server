from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.models.user import User
from app.schemas.user import UserUpdate
from app.services.auth_service import get_user_by_username


async def update_user(
    db: AsyncSession, user: User, user_in: UserUpdate
) -> User:
    updates = user_in.model_dump(exclude_unset=True)

    new_username = updates.get("username")
    if new_username is not None and new_username != user.username:
        existing = await get_user_by_username(db, new_username)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken",
            )

    for field, value in updates.items():
        if value is not None:
            setattr(user, field, value)

    await db.flush()
    await db.refresh(user)
    return user


async def change_password(
    db: AsyncSession,
    user: User,
    current_password: str,
    new_password: str,
) -> None:
    if not security.verify_password(current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if security.verify_password(new_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password",
        )

    user.hashed_password = security.hash_password(new_password)
    await db.flush()
