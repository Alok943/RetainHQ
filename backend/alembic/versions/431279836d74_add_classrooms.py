"""Add classrooms feature tables (SPEC-teacher-dashboard.md §2)

Three tables for the teacher-facing dashboard: classrooms (teacher-owned,
join-code enrollment), classroom_members (student roster, display_name
captured at join rather than the student's Google identity — see spec §5
privacy boundary), classroom_roadmaps (which catalog roadmaps a class
tracks — scopes the gap map and all class aggregates).

RLS enabled with no policies (deny-all for PostgREST/anon) on all three,
same convention as every table since migration f8a3b5c2d9e1 — the backend
connects as table owner and bypasses RLS.

Revision ID: 431279836d74
Revises: f1b3d5e7a9c0
Create Date: 2026-07-16
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "431279836d74"
down_revision: Union[str, Sequence[str], None] = "f1b3d5e7a9c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "classrooms",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("teacher_user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("school_name", sa.String(), nullable=True),
        sa.Column("join_code", sa.String(), nullable=False),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_classrooms_teacher_user_id", "classrooms", ["teacher_user_id"])
    op.create_unique_constraint("uq_classrooms_join_code", "classrooms", ["join_code"])
    op.create_index("ix_classrooms_join_code", "classrooms", ["join_code"])
    op.execute("ALTER TABLE classrooms ENABLE ROW LEVEL SECURITY")

    op.create_table(
        "classroom_members",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("classroom_id", sa.Uuid(), nullable=False),
        sa.Column("student_user_id", sa.Uuid(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("joined_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["classroom_id"], ["classrooms.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("classroom_id", "student_user_id", name="uq_class_student"),
    )
    op.create_index("ix_classroom_members_student_user_id", "classroom_members", ["student_user_id"])
    op.execute("ALTER TABLE classroom_members ENABLE ROW LEVEL SECURITY")

    op.create_table(
        "classroom_roadmaps",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("classroom_id", sa.Uuid(), nullable=False),
        sa.Column("roadmap_id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["classroom_id"], ["classrooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["roadmap_id"], ["roadmaps.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("classroom_id", "roadmap_id", name="uq_class_roadmap"),
    )
    op.execute("ALTER TABLE classroom_roadmaps ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_table("classroom_roadmaps")
    op.drop_index("ix_classroom_members_student_user_id", table_name="classroom_members")
    op.drop_table("classroom_members")
    op.drop_index("ix_classrooms_join_code", table_name="classrooms")
    op.drop_constraint("uq_classrooms_join_code", "classrooms", type_="unique")
    op.drop_index("ix_classrooms_teacher_user_id", table_name="classrooms")
    op.drop_table("classrooms")
