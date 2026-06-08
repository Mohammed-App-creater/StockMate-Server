from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.user import PasswordChange, UserResponse, UserUpdate
from app.services import user_service

# Prefix ("/users") and tags are applied in main.include_router.
router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return await user_service.update_user(db, current_user, user_in)


@router.post("/me/change-password")
async def change_current_user_password(
    payload: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    await user_service.change_password(
        db, current_user, payload.current_password, payload.new_password
    )
    return {"message": "Password changed successfully"}
