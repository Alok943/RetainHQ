"""
Syllabus upload → personal roadmap.

Two-step, review-before-commit flow (deliberate — do not collapse into one call):
  1. POST /extract       — PDF upload → LLM → DRAFT roadmap JSON. Nothing is saved.
     POST /extract-text  — pasted syllabus text → same DRAFT (token-cheap path).
  2. POST /commit   — the user-edited draft → Roadmap + RoadmapNodes owned by
                      the caller (roadmaps.user_id). Nodes are plain topics with
                      no lesson content; they exist to be logged against, which
                      feeds the FSRS review loop.

Plus DELETE /{roadmap_id} for personal roadmaps only (official catalog is
untouchable here). Extraction is gated on the selected provider's API key
(extract routes 404 without it; commit still works so a drafted-but-unsaved
roadmap never strands).
"""
import uuid
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.core.security import SupabaseUser
from app.models.models import Roadmap, RoadmapNode, Activity, UserPref
from app.schemas.syllabus import SyllabusCommitIn, SyllabusCommitOut, SyllabusQuotaOut, SyllabusTextIn
from app.services.syllabus import (
    extract_roadmap_from_pdf,
    extract_roadmap_from_text,
    extraction_configured,
    SyllabusDraft,
    SyllabusError,
)

router = APIRouter()

# Per-user daily extraction counter. In-memory is fine for the single-instance
# Render deploy (resets on redeploy, which only ever relaxes the limit) — this
# is an API-budget guard, not a security boundary.
_extract_counts: dict[str, tuple[date, int]] = {}


def _check_and_bump_daily_limit(user_id: str) -> None:
    today = datetime.utcnow().date()
    day, count = _extract_counts.get(user_id, (today, 0))
    if day != today:
        count = 0
    if count >= settings.SYLLABUS_DAILY_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily limit of {settings.SYLLABUS_DAILY_LIMIT} syllabus extractions reached — try again tomorrow.",
        )
    _extract_counts[user_id] = (today, count + 1)


@router.post("/extract", response_model=SyllabusDraft)
async def extract_syllabus(
    file: UploadFile = File(...),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Turn an uploaded syllabus PDF into a draft roadmap. Saves nothing —
    the client shows the draft for editing and commits it separately."""
    if not extraction_configured():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Syllabus upload is disabled")

    if (file.content_type or "") != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload a PDF file.")

    max_bytes = settings.SYLLABUS_MAX_PDF_MB * 1024 * 1024
    pdf_bytes = await file.read()
    if len(pdf_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"PDF is too large — the limit is {settings.SYLLABUS_MAX_PDF_MB} MB.",
        )
    if not pdf_bytes.startswith(b"%PDF"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="That file doesn't look like a PDF.")

    _check_and_bump_daily_limit(current_user.id)

    try:
        return await extract_roadmap_from_pdf(pdf_bytes)
    except SyllabusError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


@router.post("/extract-text", response_model=SyllabusDraft)
async def extract_syllabus_text(
    body: SyllabusTextIn,
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Pasted syllabus text → draft roadmap. Same contract as /extract but far
    cheaper per call (plain text has no per-page document tokens). Shares the
    daily limit with the PDF path — it's one API budget, not two."""
    if not extraction_configured():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Syllabus upload is disabled")

    _check_and_bump_daily_limit(current_user.id)

    try:
        return await extract_roadmap_from_text(body.text)
    except SyllabusError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


async def _ensure_pref_row(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Make sure a user_prefs row exists so the atomic quota UPDATE has a target."""
    exists = (
        await db.execute(select(UserPref.user_id).where(UserPref.user_id == user_id))
    ).scalar_one_or_none()
    if not exists:
        db.add(UserPref(user_id=user_id))
        await db.flush()


@router.get("/quota", response_model=SyllabusQuotaOut)
async def get_syllabus_quota(
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Lifetime personal-roadmap quota for the caller (drives the upload-page UI)."""
    user_id = uuid.UUID(current_user.id)
    used = (
        await db.execute(
            select(UserPref.custom_roadmaps_created).where(UserPref.user_id == user_id)
        )
    ).scalar_one_or_none() or 0
    limit = settings.SYLLABUS_LIFETIME_LIMIT
    return SyllabusQuotaOut(used=used, limit=limit, remaining=max(0, limit - used))


@router.post("/commit", response_model=SyllabusCommitOut, status_code=status.HTTP_201_CREATED)
async def commit_syllabus(
    body: SyllabusCommitIn,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Persist the user-edited draft as a personal roadmap (+ nodes).

    Enforces the LIFETIME cap (SYLLABUS_LIFETIME_LIMIT): the counter on
    user_prefs is claimed atomically (UPDATE … WHERE count < limit) so two
    concurrent commits can't both slip under it, and it never decrements —
    deleting a roadmap doesn't refund quota.
    """
    user_id = uuid.UUID(current_user.id)

    units = [u for u in body.units if u.topics]
    if not units:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The roadmap has no topics.")

    await _ensure_pref_row(db, user_id)
    claimed = await db.execute(
        update(UserPref)
        .where(
            UserPref.user_id == user_id,
            UserPref.custom_roadmaps_created < settings.SYLLABUS_LIFETIME_LIMIT,
        )
        .values(custom_roadmaps_created=UserPref.custom_roadmaps_created + 1)
    )
    if claimed.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"You've used all {settings.SYLLABUS_LIFETIME_LIMIT} of your custom roadmaps — "
                "that limit is lifetime, so make each one count."
            ),
        )

    # Personal roadmaps inherit the creator's audience so they appear in the
    # catalog view they actually use. slug stays NULL (globally unique column;
    # personal roadmaps route by UUID).
    audience = (
        await db.execute(select(UserPref.audience).where(UserPref.user_id == user_id))
    ).scalar_one_or_none() or "career"

    roadmap = Roadmap(
        title=body.title.strip(),
        description=body.description.strip() or None,
        audience=audience,
        user_id=user_id,
    )
    db.add(roadmap)
    await db.flush()  # roadmap.id for the node FKs

    order = 0
    total = 0
    for unit in units:
        for topic in unit.topics:
            db.add(
                RoadmapNode(
                    roadmap_id=roadmap.id,
                    phase=unit.title.strip(),
                    section=unit.title.strip(),
                    title=topic.title.strip(),
                    description=topic.description.strip() or None,
                    order_index=order,
                )
            )
            order += 1
            total += 1

    await db.commit()
    return SyllabusCommitOut(roadmap_id=roadmap.id, total_nodes=total)


@router.delete("/{roadmap_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_personal_roadmap(
    roadmap_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Delete one of the caller's personal roadmaps. Official catalog roadmaps
    (user_id NULL) are never deletable here — the ownership filter excludes them."""
    user_id = uuid.UUID(current_user.id)

    roadmap = (
        await db.execute(
            select(Roadmap).where(Roadmap.id == roadmap_id, Roadmap.user_id == user_id)
        )
    ).scalar_one_or_none()
    if not roadmap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")

    # Activities keep their card + review history but drop the roadmap/node link
    # (those FKs have no CASCADE — nulling them preserves the user's memory data).
    node_ids = select(RoadmapNode.id).where(RoadmapNode.roadmap_id == roadmap_id)
    await db.execute(
        update(Activity)
        .where(Activity.user_id == user_id, Activity.node_id.in_(node_ids))
        .values(node_id=None)
    )
    await db.execute(
        update(Activity)
        .where(Activity.user_id == user_id, Activity.roadmap_id == roadmap_id)
        .values(roadmap_id=None)
    )
    # Nodes, their prerequisite edges, and user_progress rows all CASCADE.
    await db.execute(delete(Roadmap).where(Roadmap.id == roadmap_id))
    await db.commit()
