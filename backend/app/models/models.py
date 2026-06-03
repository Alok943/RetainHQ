import uuid
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class Roadmap(SQLModel, table=True):
    __tablename__ = "roadmaps"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    nodes: List["RoadmapNode"] = Relationship(back_populates="roadmap")

class RoadmapNode(SQLModel, table=True):
    __tablename__ = "roadmap_nodes"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    roadmap_id: uuid.UUID = Field(foreign_key="roadmaps.id", ondelete="CASCADE")
    phase: str
    section: str
    title: str
    tier: Optional[str] = None
    order_index: int = Field(default=0)
    description: Optional[str] = None
    # Self-reference: subtopics are child nodes (parent_id -> a top-level node)
    parent_id: Optional[uuid.UUID] = Field(default=None, foreign_key="roadmap_nodes.id", ondelete="CASCADE")

    roadmap: Optional[Roadmap] = Relationship(back_populates="nodes")
    progress: List["UserProgress"] = Relationship(back_populates="node")

class UserProgress(SQLModel, table=True):
    __tablename__ = "user_progress"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID
    node_id: uuid.UUID = Field(foreign_key="roadmap_nodes.id", ondelete="CASCADE")
    status: str = Field(default="not_started")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    node: Optional[RoadmapNode] = Relationship(back_populates="progress")

class Track(SQLModel, table=True):
    __tablename__ = "tracks"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    activities: List["Activity"] = Relationship(back_populates="track")

class Activity(SQLModel, table=True):
    __tablename__ = "activities"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID
    track_id: Optional[uuid.UUID] = Field(default=None, foreign_key="tracks.id")
    topic: str
    notes: Optional[str] = None
    difficulty: int = Field(ge=1, le=5)
    needed_hint: bool = Field(default=False)
    key_memory: str
    mistake: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    track: Optional[Track] = Relationship(back_populates="activities")
    reviews: List["Review"] = Relationship(back_populates="activity")

class Review(SQLModel, table=True):
    __tablename__ = "reviews"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID
    activity_id: uuid.UUID = Field(foreign_key="activities.id", ondelete="CASCADE")
    status: str = Field(default="due") # 'due', 'completed'
    scheduled_for: datetime
    completed_at: Optional[datetime] = None
    rating: Optional[str] = None # 'easy', 'medium', 'hard' (subjective: how hard it felt)
    recalled: Optional[bool] = None # objective: did they reconstruct it? (got-it / missed-it)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    activity: Optional[Activity] = Relationship(back_populates="reviews")
