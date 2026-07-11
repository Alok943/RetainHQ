import uuid
from typing import List
from pydantic import BaseModel, Field


class TopicIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=500)


class UnitIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    topics: List[TopicIn] = Field(default_factory=list, max_length=60)


class SyllabusCommitIn(BaseModel):
    """The user-edited draft, committed as a personal roadmap. Same shape the
    extract endpoint returns, so the frontend round-trips it after editing."""
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=500)
    units: List[UnitIn] = Field(min_length=1, max_length=40)


class SyllabusCommitOut(BaseModel):
    roadmap_id: uuid.UUID
    total_nodes: int
