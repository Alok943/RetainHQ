import uuid
from typing import Optional
from pydantic import BaseModel, Field, field_validator

# Client-writable event types. Server-side producers (syllabus commit, etc.)
# call record_metric_event() directly and aren't bound by this list — it only
# gates the POST /api/metrics/events endpoint, so an arbitrary client can't
# write arbitrary event_type strings into the table.
CLIENT_EVENT_TYPES = {"review_depth_chosen", "companion_consent"}

MAX_PAYLOAD_BYTES = 2048


class MetricEventIn(BaseModel):
    event_type: str
    entity_id: Optional[uuid.UUID] = None
    payload: dict = Field(default_factory=dict)

    @field_validator("event_type")
    @classmethod
    def _allowlisted(cls, v: str) -> str:
        if v not in CLIENT_EVENT_TYPES:
            raise ValueError(f"event_type must be one of {sorted(CLIENT_EVENT_TYPES)}")
        return v

    @field_validator("payload")
    @classmethod
    def _bounded(cls, v: dict) -> dict:
        import json

        if len(json.dumps(v)) > MAX_PAYLOAD_BYTES:
            raise ValueError(f"payload exceeds {MAX_PAYLOAD_BYTES} bytes")
        return v
