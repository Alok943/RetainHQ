"""Per-user platform preferences (the school/career audience switch).

GET returns the stored preference plus `is_set` so the frontend knows whether to
show the one-time onboarding picker (missing row = not chosen yet, treated as
'career'). PUT upserts — used by both the onboarding picker and the Profile switcher.
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Literal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.core.security import SupabaseUser
from app.models.models import UserPref

router = APIRouter()


class PrefsOut(BaseModel):
    audience: str
    is_set: bool


class PrefsUpdate(BaseModel):
    audience: Literal["career", "school"]


@router.get("/", response_model=PrefsOut)
async def get_prefs(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    user_id = uuid.UUID(current_user.id)
    pref = (
        await db.execute(select(UserPref).where(UserPref.user_id == user_id))
    ).scalar_one_or_none()
    if pref is None:
        return PrefsOut(audience="career", is_set=False)
    return PrefsOut(audience=pref.audience, is_set=True)


@router.put("/", response_model=PrefsOut)
async def update_prefs(
    payload: PrefsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    user_id = uuid.UUID(current_user.id)
    pref = (
        await db.execute(select(UserPref).where(UserPref.user_id == user_id))
    ).scalar_one_or_none()
    if pref is None:
        pref = UserPref(user_id=user_id, audience=payload.audience)
        db.add(pref)
    else:
        pref.audience = payload.audience
        pref.updated_at = datetime.utcnow()
    await db.commit()
    return PrefsOut(audience=pref.audience, is_set=True)
