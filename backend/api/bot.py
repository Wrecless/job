from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.base import get_session
from backend.db.models import User
from backend.dependencies import get_current_user
from backend.schemas.bot import BotRunResponse
from backend.services.bot import run_job_bot

router = APIRouter(prefix="/bot", tags=["bot"])


@router.post("/run", response_model=BotRunResponse)
async def run_bot(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> BotRunResponse:
    _ = current_user
    result = await run_job_bot(session)
    return BotRunResponse(**result)
