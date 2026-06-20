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
    prerequisites: List[uuid.UUID] = []  # node ids that must come before this one
    unlocks: List[uuid.UUID] = []         # node ids this one is a prerequisite for


class RoadmapDetailOut(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    total_nodes: int = 0
    done_nodes: int = 0
    progress_pct: int = 0
    nodes: List[RoadmapNodeOut] = []


class BlockerOut(BaseModel):
    node_id: uuid.UUID
    title: str
    section: str
    unlocks_count: int            # how many incomplete topics this transitively unblocks
    unlocks_sample: List[str] = []  # a few of those downstream titles


class BlockersOut(BaseModel):
    roadmap_id: uuid.UUID
    total_incomplete: int = 0
    blockers: List[BlockerOut] = []


class ProgressUpdate(BaseModel):
    status: str  # 'done' | 'not_started'


class ProgressResult(BaseModel):
    node_id: uuid.UUID
    status: str
