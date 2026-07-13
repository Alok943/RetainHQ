import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.core.security import SupabaseUser
from app.schemas.metrics import MetricEventIn
from app.services.metrics import record_metric_event

router = APIRouter()


@router.post("/events", status_code=status.HTTP_204_NO_CONTENT)
async def create_metric_event(
    body: MetricEventIn,
    db: AsyncSession = Depends(get_db),
    current_user: SupabaseUser = Depends(get_current_user),
):
    """Allowlisted client-side metric capture (see CLIENT_EVENT_TYPES) —
    everything else goes through record_metric_event() server-side."""
    user_id = uuid.UUID(current_user.id)
    await record_metric_event(db, user_id, body.event_type, payload=body.payload, entity_id=body.entity_id)
    await db.commit()
