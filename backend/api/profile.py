import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_current_user
from backend.db.base import get_session
from backend.db.models import User, Profile
from backend.schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/", response_model=ProfileResponse)
async def get_profile(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProfileResponse:
    result = await session.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    if profile is None:
        profile = Profile(
            id=uuid.uuid4(),
            user_id=current_user.id,
        )
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
    
    return ProfileResponse.model_validate(profile)


@router.post("/", response_model=ProfileResponse)
async def create_profile(
    profile_data: ProfileCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProfileResponse:
    result = await session.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already exists. Use PUT to update.",
        )
    
    profile = Profile(
        id=uuid.uuid4(),
        user_id=current_user.id,
        **profile_data.model_dump(),
    )
    
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    
    return ProfileResponse.model_validate(profile)


@router.put("/", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProfileResponse:
    result = await session.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    if profile is None:
        profile = Profile(
            id=uuid.uuid4(),
            user_id=current_user.id,
        )
        session.add(profile)
    
    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    await session.commit()
    await session.refresh(profile)
    
    return ProfileResponse.model_validate(profile)


@router.patch("/", response_model=ProfileResponse)
async def patch_profile(
    profile_data: ProfileUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProfileResponse:
    return await update_profile(profile_data, session, current_user)
