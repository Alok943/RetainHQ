import uuid
from datetime import datetime, date
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint, Column, JSON, Index, text
from sqlalchemy.dialects.postgresql import JSONB

# JSONB in Postgres (indexable, typed); plain JSON under SQLite so the test
# suite's create_all() can build the schema. Postgres path is unchanged.
_JSONB = JSONB().with_variant(JSON(), "sqlite")

class Roadmap(SQLModel, table=True):
    __tablename__ = "roadmaps"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # Human-readable URL identifier (e.g. "aptitude", "python-swe"). Matches the
    # content folder key so a lesson URL reads /roadmaps/<slug>/learn/<lesson-slug>.
    # Nullable + unique: routes resolve by slug OR id, so old UUID links still work.
    slug: Optional[str] = Field(default=None, unique=True, index=True)
    title: str
    description: Optional[str] = None
    # Platform split: 'career' (placement/college roadmaps) | 'school' (Class 9-10 NCERT).
    # GET /api/roadmaps/ filters by the caller's user_prefs.audience. Migration c4d7e9a2b501.
    audience: str = Field(default="career")
    # NULL = official catalog roadmap. Non-NULL = personal roadmap created by this
    # user via the syllabus-upload flow — visible only to its owner. Migration a1c5e8f2d7b3.
    user_id: Optional[uuid.UUID] = Field(default=None, index=True)
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

class RoadmapNodePrerequisite(SQLModel, table=True):
    """Directed dependency edge between two nodes in the SAME roadmap:
    `node_id` requires `prerequisite_node_id` to be understood first. Powers the
    dependency graph + root-cause diagnosis ("you failed Decorators -> the likely
    blocker is Closures"). Edges are seeded by title (node UUIDs are regenerated
    on every node re-seed), see seed_*_prereqs.py."""
    __tablename__ = "roadmap_node_prerequisites"
    __table_args__ = (UniqueConstraint("node_id", "prerequisite_node_id", name="uq_node_prereq"),)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    node_id: uuid.UUID = Field(foreign_key="roadmap_nodes.id", ondelete="CASCADE")
    prerequisite_node_id: uuid.UUID = Field(foreign_key="roadmap_nodes.id", ondelete="CASCADE")

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
    # Optional link to the roadmap this capture belongs to (roadmap-level, not node).
    # Powers the Log form's roadmap picker + future "captures by roadmap" views.
    roadmap_id: Optional[uuid.UUID] = Field(default=None, foreign_key="roadmaps.id")
    # Optional lesson-level link: set when a card is created from a lesson via
    # "Add to reviews" (source_type='lesson'). Lets the review surface the lesson's
    # recall items and dedupes one card per (user, node). Migration a4b2e9f1c8d3.
    node_id: Optional[uuid.UUID] = Field(default=None, foreign_key="roadmap_nodes.id")
    problem_id: Optional[uuid.UUID] = Field(default=None, foreign_key="problems.id")
    language: Optional[str] = None
    # The user's own solution, pasted at log time. Optional; NULL = not shared.
    # Immutable per card — the card's questions are generated against it, so
    # editing it would leave them describing code that no longer exists.
    solution_code: Optional[str] = None
    # What that code actually does, inferred once at log time and resolved
    # against the closed roadmap vocabulary (services/approach_inference.py).
    # INFERENCE, deliberately kept out of `node_id`: `node_id` stays the
    # catalog's role='primary' concept and remains the only mastery-routing key
    # (SPEC-leetcode-retention.md §3.2.-1 defers approach-based routing until
    # shadow-mode validation). This pair only reframes question generation.
    approach_node_id: Optional[uuid.UUID] = Field(default=None, foreign_key="roadmap_nodes.id")
    approach_confidence: Optional[str] = None  # 'high' | 'medium' | 'low' — band, never a float
    approach_summary: Optional[dict] = Field(default=None, sa_column=Column(_JSONB))
    topic: str
    notes: Optional[str] = None
    difficulty: int = Field(ge=1, le=5)
    needed_hint: bool = Field(default=False)
    key_memory: str
    mistake: Optional[str] = None
    source_type: Optional[str] = None  # e.g. problem/lecture/video/book/article/course/project/other
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Spaced-repetition memory state (one activity = one card). Updated on each
    # review completion. See services/scheduler.py.
    # FSRS state: stability (days to target decay) + difficulty (1-10). Both NULL
    # until the first GRADED review — NULL == a brand-new card with no memory yet.
    stability: Optional[float] = None
    difficulty_fsrs: Optional[float] = None  # distinct from `difficulty` (the user's 1-5 self-rating)
    # Legacy SM-2 columns: still written so old rows/NOT NULL keep working, but
    # interval_days/last_reviewed_at/next_review_at are the live fields.
    ease_factor: float = Field(default=2.5)
    repetitions: int = Field(default=0)
    interval_days: int = Field(default=0)
    last_reviewed_at: Optional[datetime] = None  # set on each review completion
    next_review_at: Optional[datetime] = None    # mirrors the open due review (cheap dashboard queries)

    concept_card_id: Optional[uuid.UUID] = Field(default=None, foreign_key="concept_cards.id")

    track: Optional[Track] = Relationship(back_populates="activities")
    # passive_deletes=True: on an Activity delete, let the DB's ON DELETE CASCADE
    # (reviews.activity_id's FK) remove the child rows. Without this,
    # SQLAlchemy's default ORM cascade tries to disassociate children itself by
    # UPDATE-ing reviews.activity_id to NULL before the parent delete — and that
    # column is NOT NULL, so every activity delete would fail with an
    # IntegrityError the moment its reviews were loaded into the session.
    reviews: List["Review"] = Relationship(
        back_populates="activity", sa_relationship_kwargs={"passive_deletes": True}
    )

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
    quality: Optional[int] = None # SM-2 quality grade (0-5) derived from rating+recalled; persisted for analytics
    # LLM recall grader output (proposal only — user's rating/recalled stay authoritative).
    # Stored to compute the calibration metric: self-reported `recalled` vs machine `ai_recalled`.
    ai_verdict: Optional[str] = None   # 'correct' | 'partial' | 'incorrect'
    ai_recalled: Optional[bool] = None # machine judgement of whether they reconstructed the key idea
    ai_feedback: Optional[str] = None  # one short sentence shown after reveal
    # Wall-clock time from card-shown to outcome-submitted, per performance.now()
    # on the client (immune to clock skew). Clamped server-side; garbage/absent
    # values land as NULL rather than failing the completion.
    duration_ms: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    activity: Optional[Activity] = Relationship(back_populates="reviews")

class Feedback(SQLModel, table=True):
    __tablename__ = "feedbacks"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID
    message: str
    status: str = Field(default="new") # new, reviewed, resolved
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserPref(SQLModel, table=True):
    """Per-user platform preferences. `audience` picks which roadmap catalog the
    user sees ('career' = college/placement tracks, 'school' = Class 9-10 NCERT).
    Server-side (not localStorage) so the choice survives devices and sign-outs.
    A missing row means the user hasn't chosen yet — the frontend shows the
    one-time picker and the API defaults to 'career'. Migration c4d7e9a2b501."""
    __tablename__ = "user_prefs"
    user_id: uuid.UUID = Field(primary_key=True)
    audience: str = Field(default="career")  # 'career' | 'school'
    # Lifetime count of syllabus→roadmap commits — NEVER decremented (deleting a
    # roadmap doesn't refund quota). Enforces SYLLABUS_LIFETIME_LIMIT. Migration c8e2a7f5d1b9.
    custom_roadmaps_created: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TestAttempt(SQLModel, table=True):
    """One completed Tests-section session (SPEC-test-runtime.md). Question banks
    are static content (content/roadmaps/<key>/_test/*.json) — this table only
    holds the user-state outcome: what was attempted, how it went, and the score.

    `results` is a JSONB array of
    {question_id, node_title, type, outcome ('got'|'missed'|'wrong'), trap, misconception}.
    node_title (not the content slug) is the join key back to RoadmapNode.title,
    matching how ReviewResponse.node_title already works. Migration f2b7d3a9c8e4."""
    __tablename__ = "test_attempts"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID
    roadmap_id: uuid.UUID = Field(foreign_key="roadmaps.id")
    phase: str
    score: int
    max_score: int
    results: list = Field(sa_column=Column(_JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class QuestionSet(SQLModel, table=True):
    """One persisted LLM-generated question set for a card (activity).

    Generated once, then REUSED for at least QUESTION_SET_REUSE review sessions
    (served in a fresh random order each time) before a new set is generated —
    this amortizes the LLM cost across sessions and stops the quiz from changing
    under the learner every single review. `items` is a JSONB array of
    {question, reference_answer}; reference answers are the grading ground truth
    and are NEVER sent to the client. `depth` = 'main' | 'deep' (how the user
    chose to revise). Migration b3d9f1a4c6e2."""
    __tablename__ = "question_sets"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(index=True)
    activity_id: uuid.UUID = Field(foreign_key="activities.id", ondelete="CASCADE", index=True)
    depth: str = Field(default="main")  # 'main' (core points) | 'deep' (derive/apply/edge cases)
    items: list = Field(sa_column=Column(_JSONB))  # [{question, reference_answer}]
    times_used: int = Field(default=0)  # sessions this set has been served in
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReminderLog(SQLModel, table=True):
    """At-most-once-per-day ledger for due-review reminder emails. The unique
    (user_id, sent_on) constraint is the idempotency guard — a second run on the
    same day can't double-send (the INSERT conflicts)."""
    __tablename__ = "reminder_log"
    __table_args__ = (UniqueConstraint("user_id", "sent_on", name="uq_reminder_user_day"),)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID
    sent_on: date  # UTC date the reminder was sent
    due_count: int = Field(default=0)  # how many were due at send time (for later analysis)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MetricEvent(SQLModel, table=True):
    """Generic learning-analytics event store — heterogeneous/exploratory
    signals that don't warrant a dedicated table (extraction edit-deltas,
    future ad-hoc metrics). `entity_id` is a loose FK (no constraint — the
    referenced table varies by event_type) for joining back to the source row."""
    __tablename__ = "metric_events"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(index=True)
    event_type: str = Field(index=True)
    entity_id: Optional[uuid.UUID] = None
    payload: dict = Field(default_factory=dict, sa_column=Column(_JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PushSubscription(SQLModel, table=True):
    """One row per browser/device Web Push subscription. `endpoint` is unique —
    it's the browser push service's per-registration URL, so it's the natural
    upsert key (a re-subscribe from the same device/browser updates in place)."""
    __tablename__ = "push_subscriptions"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(index=True)
    endpoint: str = Field(unique=True)
    p256dh: str
    auth: str
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Classroom(SQLModel, table=True):
    """One teacher-owned classroom (SPEC-teacher-dashboard.md §2). "Is a teacher"
    == "owns >=1 classroom" — there is deliberately no user_prefs.role column.
    `join_code` is the student enrollment key (8 chars, unambiguous alphabet —
    no 0/O/1/I). `school_name` is free text for now: no school entity in v1.
    `archived_at` is a soft archive — hides the classroom from lists but keeps
    its history for analytics."""
    __tablename__ = "classrooms"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    teacher_user_id: uuid.UUID = Field(index=True)
    name: str
    school_name: Optional[str] = None
    join_code: str = Field(unique=True, index=True)
    archived_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ClassroomMember(SQLModel, table=True):
    """One student's membership in a classroom.

    Roll-call name shown to the teacher. Captured at join (student types it,
    e.g. "Priya Sharma, Roll 14") and editable by the teacher afterward. We do
    NOT surface the student's Google account name/email to the teacher — see
    SPEC-teacher-dashboard.md §5."""
    __tablename__ = "classroom_members"
    __table_args__ = (UniqueConstraint("classroom_id", "student_user_id", name="uq_class_student"),)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    classroom_id: uuid.UUID = Field(foreign_key="classrooms.id", ondelete="CASCADE")
    student_user_id: uuid.UUID = Field(index=True)
    display_name: str
    joined_at: datetime = Field(default_factory=datetime.utcnow)


class ClassroomRoadmap(SQLModel, table=True):
    """Which catalog roadmaps (subjects/chapters) this classroom tracks. The gap
    map and all class aggregates are scoped to these — a teacher never sees
    signals from a student's personal/career roadmaps."""
    __tablename__ = "classroom_roadmaps"
    __table_args__ = (UniqueConstraint("classroom_id", "roadmap_id", name="uq_class_roadmap"),)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    classroom_id: uuid.UUID = Field(foreign_key="classrooms.id", ondelete="CASCADE")
    roadmap_id: uuid.UUID = Field(foreign_key="roadmaps.id", ondelete="CASCADE")


class LearningEvent(SQLModel, table=True):
    """Immutable append-only evidence log — the source of truth for all mastery
    state (Career Coach design doc, Design law 2). Every producer (in-app review,
    manual log, and later LeetCode/GitHub/companion) writes this same shape.

    Rows are NEVER updated. Correction = insert a compensating event or soft-delete
    via `deleted_at` and recompute. Mastery in `node_mastery` is a derived cache and
    can be rebuilt from this table alone at any time."""
    __tablename__ = "learning_events"
    __table_args__ = (
        # Idempotency key for polling producers (LeetCode etc, phase 2+) — a
        # double-counted re-read of the same solve would silently inflate
        # mastery. Partial: entity_id is NULL for producers with no source row
        # (e.g. manual log), which must never collide with each other.
        Index(
            "uq_learning_event_dedupe", "user_id", "source", "entity_id",
            unique=True,
            postgresql_where=text("entity_id IS NOT NULL"),
            sqlite_where=text("entity_id IS NOT NULL"),
        ),
        Index("ix_learning_event_fold_path", "user_id", "node_id", "occurred_at"),
    )
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(index=True)
    occurred_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    event_type: str            # see evidence_weights.EVENT_TYPES
    trust_tier: str            # see evidence_weights.TRUST_TIERS
    source: str                # see evidence_weights.SOURCES
    node_id: Optional[uuid.UUID] = Field(default=None, foreign_key="roadmap_nodes.id", index=True)
    duration_min: int = Field(default=0)
    difficulty: Optional[str] = None    # 'easy' | 'medium' | 'hard'
    assistance: Optional[str] = None    # 'none' | 'hint' | 'llm_assisted' | 'solution_seen'
    outcome: Optional[str] = None       # 'pass' | 'fail' | 'partial'
    grade: Optional[float] = None       # 0.0-1.0
    # Loose FK to the producing row (reviews.id, activities.id, ...). No constraint:
    # the referenced table varies by source. Doubles as the idempotency key with
    # (user_id, source) — see uq_learning_event_dedupe.
    entity_id: Optional[uuid.UUID] = Field(default=None, index=True)
    payload: dict = Field(default_factory=dict, sa_column=Column(_JSONB))
    # Soft delete only — user-requested evidence removal (design doc §14). Excluded
    # from recompute; the row survives so history stays auditable.
    deleted_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NodeMastery(SQLModel, table=True):
    """Derived mastery cache — one row per (user, node). Recomputable in full
    from `learning_events`; deleting this table costs only CPU. Never write it
    from anywhere except services/evidence.py."""
    __tablename__ = "node_mastery"
    __table_args__ = (UniqueConstraint("user_id", "node_id", name="uq_node_mastery"),)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(index=True)
    node_id: uuid.UUID = Field(foreign_key="roadmap_nodes.id", ondelete="CASCADE", index=True)
    m_learned: float = Field(default=0.0)      # evidence-accumulated skill, 0-1
    evidence_count: int = Field(default=0)     # non-deleted, weight-bearing events folded in
    last_event_at: Optional[datetime] = None
    exposure_capped: bool = Field(default=False)  # True if only T3-capped evidence exists
    weights_version: str                       # which weights table produced this
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CareerGoal(SQLModel, table=True):
    """The user's active career target. Drives tree generation and (phase 3)
    scheduler priorities. One active goal per user — parent doc assumption A1;
    multi-goal is explicitly P2."""
    __tablename__ = "career_goals"
    __table_args__ = (
        # Enforced by the DB, not application code phase 3 might forget.
        Index(
            "uq_career_goal_one_active", "user_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
            sqlite_where=text("status = 'active'"),
        ),
    )
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(index=True)
    role_key: str                       # 'backend' | 'ai_engineer' | 'sde_generalist' — a template key
    title: str                          # user-facing, editable: "Backend SDE, Jan 2027 placements"
    target_date: Optional[date] = None  # deadline proximity input for phase 3; None = open-ended
    # The tree this goal generated. NULL only between goal creation and tree commit.
    roadmap_id: Optional[uuid.UUID] = Field(default=None, foreign_key="roadmaps.id", index=True)
    template_version: Optional[str] = None  # pinned at commit — parent §6 versioning rule
    # Parent A3: user-declared temporary weight override. Stored now, consumed in
    # phase 3. Suppresses balance flags until the end date.
    sprint_node_id: Optional[uuid.UUID] = Field(default=None, foreign_key="roadmap_nodes.id")
    sprint_until: Optional[date] = None
    # Phase 3 scheduler's daily study budget. DB CHECK enforces the 30-240
    # range; the route ALSO clamps server-side (a slider overshoot shouldn't 422).
    daily_minutes: int = Field(default=60, ge=30, le=240)
    status: str = Field(default="active")   # 'active' | 'archived'
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CareerGoalRoadmap(SQLModel, table=True):
    """A roadmap this goal draws its plan from, on top of its own generated tree.

    Nodes stay in their home roadmap — attaching creates only `node_meta` sidecar
    rows, never copies of `roadmap_nodes`. Copying would break lesson deep-links
    (which resolve /<roadmap-slug>/learn/<lesson-slug>), fork `user_progress`, and
    split FSRS history across two node ids for the same concept.

    `subject` is the balance bucket the attached nodes fold into; two roadmaps
    given the same subject merge into one bar on the balance strip.
    """
    __tablename__ = "career_goal_roadmaps"
    __table_args__ = (UniqueConstraint("goal_id", "roadmap_id", name="uq_goal_roadmap"),)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    goal_id: uuid.UUID = Field(foreign_key="career_goals.id", ondelete="CASCADE", index=True)
    roadmap_id: uuid.UUID = Field(foreign_key="roadmaps.id", ondelete="CASCADE", index=True)
    subject: str
    default_priority: int = Field(default=3, ge=1, le=5)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NodeMeta(SQLModel, table=True):
    """Career-tree-specific node attributes. Sidecar to roadmap_nodes so the
    shared catalog table stays untouched. Rows exist only for career-tree nodes."""
    __tablename__ = "node_meta"
    __table_args__ = (UniqueConstraint("node_id", name="uq_node_meta_node"),)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    node_id: uuid.UUID = Field(foreign_key="roadmap_nodes.id", ondelete="CASCADE", index=True)
    # Stable across template versions — parent §6 mandatory rule. Template-authored
    # slug ('dsa.graphs.bfs'), NOT the UUID (node UUIDs are regenerated on re-seed,
    # see the RoadmapNodePrerequisite docstring).
    stable_key: str = Field(index=True)
    priority: int = Field(default=3, ge=1, le=5)
    est_effort_min: int = Field(default=60)
    subject: str                          # top-level grouping for phase-3 balance: 'dsa' | 'os' | 'dbms' | ...
    review_policy: str = Field(default="default")  # parent A7: per-node FSRS tuning, consumed later
    user_edited: bool = Field(default=False)       # protects user edits from template upgrades
    embedding: Optional[list] = Field(default=None, sa_column=Column(_JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Problem(SQLModel, table=True):
    """Catalog of LeetCode problems (metadata only). Shared across all users."""
    __tablename__ = "problems"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_problem_source_ext"),)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    source: str = Field(default="leetcode")
    external_id: int
    slug: str
    title: str
    difficulty: str  # 'easy' | 'medium' | 'hard'
    tags: Optional[list] = Field(default=None, sa_column=Column(_JSONB))
    url: Optional[str] = None
    acceptance: Optional[float] = None
    paid_only: bool = Field(default=False)
    catalog_version: str

    concepts: List["ProblemConcept"] = Relationship(back_populates="problem")
    concept_cards: List["ConceptCard"] = Relationship(back_populates="problem")


class ProblemAlias(SQLModel, table=True):
    """Another site's slug for a problem this catalog already holds.

    NeetCode's problems ARE LeetCode's, re-slugged (`two-integer-sum` is Two
    Sum) — so a NeetCode solve is evidence about an existing `problems` row
    that the curated LeetCode mapping pass has already attached to a roadmap
    node. Aliasing inherits that mapping instead of importing a parallel
    catalog that would need its own curation and would drift from this one
    (D-071, reversing D-064's separate-catalog design).

    Generic on `source`, not NeetCode-specific: the next site is the same shape.
    """
    __tablename__ = "problem_aliases"
    __table_args__ = (UniqueConstraint("source", "alias_slug", name="uq_problem_alias_source_slug"),)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    problem_id: uuid.UUID = Field(foreign_key="problems.id", index=True)
    source: str
    alias_slug: str
    # 'slug_identical' | 'title_match' | 'override' — a wrong alias silently
    # attributes one problem's evidence to another, so keep how it was derived.
    resolved_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProblemConcept(SQLModel, table=True):
    """Mapping between a Problem and a RoadmapNode. Hand-curated via a versioned classification run."""
    __tablename__ = "problem_concepts"
    __table_args__ = (UniqueConstraint("problem_id", "node_id", name="uq_problem_concept"),)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    problem_id: uuid.UUID = Field(foreign_key="problems.id", ondelete="CASCADE")
    node_id: uuid.UUID = Field(foreign_key="roadmap_nodes.id", ondelete="CASCADE")
    role: str  # 'primary' | 'supporting' | 'alternative'
    confidence: float
    reviewed_by: Optional[str] = None  # 'human' or None
    teaching_role: Optional[str] = None  # 'canonical' | 'practice' | 'variant' | 'synthesis'
    order_in_concept: Optional[int] = None
    assumes: Optional[list] = Field(default=None, sa_column=Column(_JSONB))
    alternatives: Optional[list] = Field(default=None, sa_column=Column(_JSONB))
    mapping_version: str

    problem: Optional[Problem] = Relationship(back_populates="concepts")
    node: Optional["RoadmapNode"] = Relationship()


class ConceptCard(SQLModel, table=True):
    """Shared card bank for concept-first review. Authored once, served to all users."""
    __tablename__ = "concept_cards"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    node_id: uuid.UUID = Field(foreign_key="roadmap_nodes.id", ondelete="CASCADE")
    problem_id: Optional[uuid.UUID] = Field(default=None, foreign_key="problems.id", ondelete="CASCADE")
    card_type: str  # 'intuition' | 'complexity' | 'edge_case' | 'transfer'
    prompt: str
    model_answer: str
    discriminates_from: Optional[list] = Field(default=None, sa_column=Column(_JSONB))
    status: str = Field(default="draft")
    version: int = Field(default=1)

    node: Optional["RoadmapNode"] = Relationship()
    problem: Optional[Problem] = Relationship(back_populates="concept_cards")


class ProblemAttempt(SQLModel, table=True):
    """Manual 'I solved this' marks. Deliberately NOT evidence: the extension's
    verified-submission path writes learning_events (T1_verified_external) and
    moves node_mastery; this table never does either (IMPLEMENTATION-problem-capture.md
    §1) — it is the completion checkbox, not the evidence spine."""
    __tablename__ = "problem_attempts"
    __table_args__ = (UniqueConstraint("user_id", "problem_id", name="uq_problem_attempt"),)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(index=True)
    problem_id: uuid.UUID = Field(foreign_key="problems.id", ondelete="CASCADE", index=True)
    status: str = Field(default="solved")     # 'solved' | 'attempted'
    language: Optional[str] = None
    marked_at: datetime = Field(default_factory=datetime.utcnow)
