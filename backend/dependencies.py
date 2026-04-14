from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.db.base import get_session
from backend.db.models import User
from backend.services.auth import verify_access_token

security = HTTPBearer(auto_error=False)


async def get_personal_user(session: AsyncSession) -> User:
    settings = get_settings()
    result = await session.execute(
        select(User).where(User.email == settings.personal_user_email, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if user is not None:
        return user

    user = User(
        email=settings.personal_user_email,
        password_hash="personal-user-disabled",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    if credentials is None:
        return await get_personal_user(session)

    user_id = verify_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await session.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
