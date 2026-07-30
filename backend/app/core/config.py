from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "RetainHQ Backend"
    DEBUG: bool = False

    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_JWT_SECRET: str
    DATABASE_URL: str

    # CORS — comma-separated origins from env. Localhost included for dev convenience.
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Founder/admin gate — must be set via env (no hardcoded default).
    ADMIN_EMAIL: str

    # DEV ONLY — local auth bypass so the authenticated app can be previewed
    # without Google OAuth. Defaults False and MUST NEVER be set in production
    # (Railway). When True, get_current_user returns the DEV_USER_EMAIL account
    # (resolved from auth.users, falling back to ADMIN_EMAIL) without verifying
    # any JWT. Set DEV_USER_ID to skip the email->id lookup.
    # Guarded: requires DEBUG=true or the app refuses to start (see the
    # model_validator below) — a stray flag in prod crashes the deploy loudly
    # instead of silently handing admin access to every anonymous request.
    DEV_AUTH_BYPASS: bool = False
    DEV_USER_EMAIL: str = ""
    DEV_USER_ID: str = ""

    # DB pool tuning (match to your deploy worker count)
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    # Groq LLM recall grader (EXPERIMENT — frozen, off the launch path).
    # gpt-oss-120b: strong instruction-following + JSON for question gen/grading.
    # It's a reasoning model — grader._groq_json pins reasoning_effort=low for it.
    # Override via env (GROQ_MODEL) to fall back to e.g. llama-3.3-70b-versatile.
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GRADER_ENABLED: bool = False
    # A generated question set is served for this many review sessions (shuffled
    # each time) before a fresh set is generated — amortizes the LLM cost and
    # keeps the quiz stable while the memory is forming.
    QUESTION_SET_REUSE: int = 2

    # Syllabus → roadmap extraction. One-shot, user-visible structuring task.
    # Provider is routed by SYLLABUS_MODEL: a "gemini*" id uses Google (GEMINI_API_KEY),
    # anything else uses Anthropic (ANTHROPIC_API_KEY). The feature is a no-op (404)
    # until the SELECTED provider's key is set, so it's safe to deploy gated-off.
    # Gemini is the default provider (D-037) — GEMINI_API_KEY is the only LLM key
    # these features need. The Anthropic path stays wired so a single env override
    # (SYLLABUS_MODEL=claude-*) routes back without a code change.
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # Third provider branch: any OpenAI-compatible /chat/completions endpoint —
    # DeepSeek, Qwen/DashScope, Moonshot, Zhipu, Together, a local vLLM. Reached
    # when the model id is neither "gemini*" nor "claude*". Deliberately spoken
    # over httpx (already a dependency) rather than the `openai` SDK: this is one
    # unstreamed JSON POST, and the wire protocol is the thing that's portable,
    # not the client library.
    #
    # Structured output on this branch is `response_format={"type":"json_object"}`
    # plus the schema in the prompt — NOT strict `json_schema`, whose nested-schema
    # support varies sharply across these providers. Correctness therefore leans on
    # _validate_draft + the retry, which is exactly why the generation path is now
    # instrumented (see services/career_tree.py): swapping providers must be a
    # measurement, not a bet.
    OPENAI_COMPAT_BASE_URL: str = ""   # e.g. https://api.deepseek.com/v1
    OPENAI_COMPAT_API_KEY: str = ""
    # NOT 32000 (the Gemini path's value) — output caps here are per-vendor AND
    # per-API-tier, not a single number: DeepSeek documents 8K on its Beta API
    # while its V4 models go far higher. 8192 is a deliberately conservative
    # default that every compatible provider accepts. A 90-node tree is large, so
    # if trees start falling back, raise this FIRST: truncation surfaces as a JSON
    # parse failure, which is indistinguishable from "the model is bad" until you
    # rule it out. Checked against vendor docs 2026-07-26.
    OPENAI_COMPAT_MAX_TOKENS: int = 8192
    # gemini-3.6-flash (GA 2026-07-21) — same or lower cost than 3.5-flash per
    # Google's own benchmarks, so this is a straight upgrade, not a tradeoff.
    # e.g. "claude-opus-4-8" to route to Anthropic instead.
    SYLLABUS_MODEL: str = "gemini-3.6-flash"
    SYLLABUS_MAX_PDF_MB: int = 10
    SYLLABUS_DAILY_LIMIT: int = 5  # extractions per user per UTC day (API-budget guard)
    SYLLABUS_LIFETIME_LIMIT: int = 3  # personal roadmaps per user, LIFETIME (delete ≠ refund)

    # Teacher dashboard (SPEC-teacher-dashboard.md). Abuse bound on classroom
    # creation, same spirit as the syllabus caps above — not a pricing tier.
    MAX_CLASSROOMS_PER_TEACHER: int = 20

    # Career tree generation (SPEC-career-coach-phase2.md §3). One-shot model
    # call adapting a role template. Uses GEMINI_API_KEY — routed the same
    # "gemini*" way as SYLLABUS_MODEL (D-037).
    # Quota-exempt (it's the primary onboarding path, not abuse-prone like a
    # syllabus PDF) — rate-limited daily instead, per user.
    CAREER_TREE_MODEL: str = "gemini-3.6-flash"
    CAREER_TREE_DAILY_LIMIT: int = 3

    # Companion (services/llm_classifier.py, services/topic_segmentation.py):
    # ingesting a whole session/chat and picking cheap structured labels
    # (which node, which topics) is exactly the kind of high-volume,
    # low-reasoning call a lite-tier model is for — the heavier models
    # (SYLLABUS_MODEL/CAREER_TREE_MODEL above) stay reserved for the one-shot
    # generation work that actually needs them.
    #
    # DELIBERATELY NOT bumped to gemini-3.6-flash alongside the two above.
    # Checked 2026-07-27: Google's 2026-07-21 release shipped gemini-3.6-flash
    # (the mid-tier model, replacing 3.5-flash) and gemini-3.5-flash-lite (the
    # lite tier — still versioned 3.5; Google did not release a 3.6 lite
    # variant). "gemini-3.6-flash-lite" does not exist. Setting this to
    # gemini-3.6-flash instead of the lite tier would be a straight 5x/3x
    # input/output cost increase on every companion sync for no benefit —
    # ingestion/classification doesn't need mid-tier reasoning. Override via
    # env once a newer lite-tier id is confirmed to actually exist; don't
    # guess one in.
    COMPANION_LITE_MODEL: str = "gemini-3.5-flash-lite"

    # Due-review reminder emails (Resend). Feature is a no-op until RESEND_API_KEY
    # is set, so it's safe to deploy gated-off. CRON_SECRET guards the trigger
    # endpoint — if unset, the endpoint refuses all callers (no open trigger).
    RESEND_API_KEY: str = ""
    RESEND_FROM: str = "RetainHQ <reviews@retainhq.app>"
    CRON_SECRET: str = ""
    APP_BASE_URL: str = "https://retainhq.app"  # used to build the one-tap review link

    # Server-side PostHog (app.services.analytics). Same project as the frontend
    # (posthog-js), keyed by the Supabase user id so client + server events unify.
    # No-op until POSTHOG_API_KEY is set, so it's safe to deploy gated-off.
    POSTHOG_API_KEY: str = ""
    POSTHOG_HOST: str = "https://us.i.posthog.com"  # EU: https://eu.i.posthog.com

    # Sentry error tracking. No-op until SENTRY_DSN is set (main.py gates init on
    # it). Pseudonymous only — send_default_pii stays False; deps.get_current_user
    # sets only the Supabase user id, never email.
    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = "development"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    # Web Push (VAPID). No-op until both keys are set — generate once locally
    # with `vapid --gen` (py-vapid, installs with pywebpush); both keys live in
    # Render only. The public key is served to the frontend via
    # GET /api/push/vapid-public-key (single source of truth, avoids a
    # Vercel/Render key-sync hazard).
    VAPID_PRIVATE_KEY: str = ""
    VAPID_PUBLIC_KEY: str = ""
    VAPID_SUBJECT: str = "mailto:reviews@retainhq.app"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def _refuse_auth_bypass_outside_dev(self) -> "Settings":
        # DEV_AUTH_BYPASS makes EVERY request the dev account (which defaults to
        # ADMIN_EMAIL) with no JWT — one stray env var in prod would hand admin
        # access to anyone. Fail the boot loudly instead of trusting a comment:
        # the bypass only works when DEBUG is also on (a combo prod never has).
        if self.DEV_AUTH_BYPASS and not self.DEBUG:
            raise RuntimeError(
                "DEV_AUTH_BYPASS=true requires DEBUG=true. This flag disables all "
                "authentication and impersonates the admin — it must never be set "
                "in production. Set DEBUG=true in your local .env, or remove "
                "DEV_AUTH_BYPASS."
            )
        return self

settings = Settings()
