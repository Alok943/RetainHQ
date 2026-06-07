from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.api.deps import get_db, get_admin_user
from app.core.security import SupabaseUser
from app.schemas.admin import AdminFunnel, FunnelSummary, FunnelUser, SourceCount, AdminFeedbackOut

router = APIRouter()

# Activation funnel derived from existing data (auth.users + activities + reviews).
# Mirrors docs/funnel.sql. Admin-gated (founder email) — no per-user PII leaves the
# admin's own view. Casts pct to float so Pydantic serializes cleanly.
_SUMMARY_SQL = text("""
with u as (select id, created_at::date as signup_date from auth.users),
acted    as (select distinct user_id from activities),
reviewed as (select distinct user_id from reviews where status = 'completed'),
returned as (
  select u.id from u
  where exists (select 1 from activities a where a.user_id = u.id and a.created_at::date  > u.signup_date)
     or exists (select 1 from reviews r where r.user_id = u.id and r.completed_at::date > u.signup_date)
)
select
  (select count(*) from u)        as signups,
  (select count(*) from acted)    as logged_activity,
  (select count(*) from reviewed) as completed_review,
  (select count(*) from returned) as returned_later_day,
  round(100.0 * (select count(*) from acted)    / nullif((select count(*) from u), 0), 1)::float as pct_activated,
  round(100.0 * (select count(*) from reviewed) / nullif((select count(*) from u), 0), 1)::float as pct_reviewed,
  round(100.0 * (select count(*) from returned) / nullif((select count(*) from u), 0), 1)::float as pct_retained
""")

_USERS_SQL = text("""
select
  u.email,
  u.created_at::date                                       as signed_up,
  count(distinct a.id)                                     as activities,
  count(distinct r.id) filter (where r.status='completed') as reviews_done,
  greatest(max(a.created_at), max(r.completed_at))::date   as last_active
from auth.users u
left join activities a on a.user_id = u.id
left join reviews   r on r.user_id = u.id
group by u.email, u.created_at
order by u.created_at desc
""")

_SOURCE_SQL = text("""
select coalesce(source_type, 'unspecified') as source_type, count(*) as activities
from activities
group by 1
order by 2 desc
""")


@router.get("/funnel", response_model=AdminFunnel)
async def get_funnel(
    db: AsyncSession = Depends(get_db),
    admin: SupabaseUser = Depends(get_admin_user),
):
    summary = (await db.execute(_SUMMARY_SQL)).mappings().first()
    users = (await db.execute(_USERS_SQL)).mappings().all()
    sources = (await db.execute(_SOURCE_SQL)).mappings().all()
    return AdminFunnel(
        summary=FunnelSummary(**summary),
        users=[FunnelUser(**u) for u in users],
        by_source=[SourceCount(**s) for s in sources],
    )

_FEEDBACK_SQL = text("""
select
  f.id,
  u.email,
  f.message,
  f.status,
  f.created_at
from feedbacks f
left join auth.users u on u.id = f.user_id
order by f.created_at desc
""")

@router.get("/feedback", response_model=list[AdminFeedbackOut])
async def get_feedback(
    db: AsyncSession = Depends(get_db),
    admin: SupabaseUser = Depends(get_admin_user),
):
    feedbacks = (await db.execute(_FEEDBACK_SQL)).mappings().all()
    return [AdminFeedbackOut(**f) for f in feedbacks]
