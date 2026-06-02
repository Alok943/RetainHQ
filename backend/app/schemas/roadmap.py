from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
import uuid


class RoadmapListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: Optional[str] = None
    total_nodes: int = 0
    done_nodes: int = 0
    progress_pct: int = 0


class RoadmapNodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    phase: str
    section: str
    title: str
    tier: Optional[str] = None
    order_index: int
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    status: str = "not_started"  # 'done' | 'not_started'


class RoadmapDetailOut(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    total_nodes: int = 0
    done_nodes: int = 0
    progress_pct: int = 0
    nodes: List[RoadmapNodeOut] = []


class ProgressUpdate(BaseModel):
    status: str  # 'done' | 'not_started'


class ProgressResult(BaseModel):
    node_id: uuid.UUID
    status: str
