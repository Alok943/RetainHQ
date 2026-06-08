# Session Handoff — RetainHQ

Paste this into a new Claude session: **"Read docs/SESSION_HANDOFF.md and CLAUDE.md, then we'll continue."**
`CLAUDE.md` is the source of truth for architecture/conventions/status — this file only carries the **deltas and open loops** the long previous session ended on.

## Where things stand
- Core loop is fully live end-to-end: **Log → Day-0 baseline review → SM-2 schedule → retrieval-gate review → Vault/Home/Analytics**.
- Shipped recently (all committed, details in CLAUDE.md): SM-2 scheduling, Knowledge Vault + `GET /api/activities/`, `source_type` field + Vault badge, **Admin** page (founder-gated funnel + feedback), user feedback flow, and the **Tier-0/1/2 hardening** (HS256 removed, `echo=settings.DEBUG`, env-driven CORS, required `ADMIN_EMAIL`, input length limits, atomic review-complete, `user_progress` unique index, CHECK constraints, indexes, SM-2 interval cap). DB is at alembic head `73c79267ec74`.
- Working tree is **clean**; latest commits are onboarding-guide + coming-soon banners (added in Antigravity/Gemini, **not yet reviewed by Claude**).

## Open loops / next up
1. **Deploy** (the main next step). Not deployed yet. Options discussed: AWS **Amplify (frontend) + Lambda/API-Gateway via Mangum (backend, free-forever)** or EC2 t3.micro; or the simpler Vercel + Render/Railway. Deploy env vars needed: `DEBUG=false`, `ADMIN_EMAIL=aloksingh98541@gmail.com`, `CORS_ORIGINS=<frontend-url>`, plus existing `DATABASE_URL`/`SUPABASE_*`. Run `alembic upgrade head` on deploy.
2. **Review the new committed files** `frontend/src/OnboardingGuide.jsx` and `frontend/src/ComingSoon.jsx` — Claude hasn't seen them. (User mentioned an "Observability.jsx" that does **not** exist in the repo — likely meant one of these.)
3. **Login hero spacing** — `Login.jsx` hero padding was reduced (`pb-20`→`pb-10`, `pt-16`→`pt-12`) so the "The learning loop, automated" heading peeks at the bottom of the first view and sits above the cards on scroll. **Visually unverified at the user's real viewport** — confirm it peeks (not fully buried, not cramped).
4. **Remaining hardening** — see `docs/hardening-plan.md`. Tier 0 done; Tier 3 items (rate limiting, activity pagination, dashboard CTE, etc.) are deliberately deferred until scaling past the first cohort. Note: `datetime.utcnow()` migration is intentionally **deferred** (naive-UTC is consistent; don't do a naive→aware find-replace).
5. **Walkthrough/demo** — production guide at `docs/walkthrough-guide.md` (record after deploy).

## How the user wants to work (respect this)
- **Division of labor:** Claude = plan / review / decide / debug. **Gemini 3 Pro in Antigravity = implements** the plans Claude writes. After Gemini implements, **start a fresh Claude session** to review (don't keep one thread alive — it re-bills the whole transcript).
- **Model effort:** high effort **only** for decisions/planning/review. When handing off implementation, **state the level** ("switch to low/medium for this"). Mechanical edits → low.
- **Token discipline:** short single-purpose sessions, `/clear` between tasks, share screenshots sparingly (they re-bill every turn).
- **Commits:** authored **solely by the user — NO `Co-Authored-By: Claude` trailer**. Work on `main`.
- **Verification:** backend via `backend/.venv` Python + alembic; frontend via the preview MCP (only the public Login page renders without auth — everything else needs Google OAuth, so compile-checks are the automated proof). Supabase read-only MCP for DB checks.

## Key docs
- `CLAUDE.md` — architecture, conventions, data model, API, status.
- `docs/FLOWS.md` — every screen's UI→API→DB flow.
- `docs/hardening-plan.md` — security/scalability backlog (triaged).
- `docs/funnel.sql` — activation funnel SQL (also exposed via `/api/admin/funnel`).
- `docs/walkthrough-guide.md` — demo recording guide.
