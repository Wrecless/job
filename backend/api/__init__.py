from fastapi import APIRouter

from backend.api import auth
from backend.api.resume import router as resume_router
from backend.api.profile import router as profile_router

__all__ = ["auth", "resume_router", "profile_router"]
