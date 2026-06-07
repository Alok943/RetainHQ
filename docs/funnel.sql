-- ============================================================
-- RetainHQ — Activation Funnel (run in the Supabase SQL editor)
-- ------------------------------------------------------------
-- Derived entirely from existing data: auth.users + activities + reviews.
-- No instrumentation, no new tables. Re-run anytime to refresh.
-- Founder-facing: the SQL editor runs as admin (reads auth.users), so this
-- needs no in-app admin gating. An in-app endpoint can pair with admin login later.
-- ============================================================


-- 1) FUNNEL SUMMARY ------------------------------------------------------------
-- signup -> logged an activity -> completed a review -> returned on a LATER day.
-- "returned_later_day" is the cheapest retention proxy: did the user do anything
-- on a calendar day after they signed up.
with u as (
  select id, created_at::date as signup_date from auth.users
),
acted    as (select distinct user_id from activities),
reviewed as (select distinct user_id from reviews where status = 'completed'),
returned as (
  select u.id
  from u
  where exists (select 1 from activities a
                where a.user_id = u.id and a.created_at::date  > u.signup_date)
     or exists (select 1 from reviews r
                where r.user_id = u.id and r.completed_at::date > u.signup_date)
)
select
  (select count(*) from u)        as signups,
  (select count(*) from acted)    as logged_activity,
  (select count(*) from reviewed) as completed_review,
  (select count(*) from returned) as returned_later_day,
  round(100.0 * (select count(*) from acted)    / nullif((select count(*) from u), 0), 1) as pct_activated,  -- logged / signups
  round(100.0 * (select count(*) from reviewed) / nullif((select count(*) from u), 0), 1) as pct_reviewed,   -- reviewed / signups
  round(100.0 * (select count(*) from returned) / nullif((select count(*) from u), 0), 1) as pct_retained;   -- returned / signups


-- 2) PER-USER BREAKDOWN --------------------------------------------------------
-- Useful while the cohort is small (~20). Rows with activities = 0 are the
-- biggest leak: signed up but never logged.
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
order by u.created_at desc;


-- 3) CAPTURES BY SOURCE TYPE ---------------------------------------------------
-- Populates as users log with the new Source Type field. Foundation for a future
-- "retention by source" report (e.g. do projects stick better than videos?).
select coalesce(source_type, 'unspecified') as source_type, count(*) as activities
from activities
group by 1
order by 2 desc;
