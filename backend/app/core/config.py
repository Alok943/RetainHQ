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
    # Gemini is wired in to A/B the extraction quality/cost against Opus.
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    SYLLABUS_MODEL: str = "claude-opus-4-8"  # e.g. "gemini-flash-lite-latest" to route to Gemini
    SYLLABUS_MAX_PDF_MB: int = 10
    SYLLABUS_DAILY_LIMIT: int = 5  # extractions per user per UTC day (API-budget guard)
    SYLLABUS_LIFETIME_LIMIT: int = 3  # personal roadmaps per user, LIFETIME (delete ≠ refund)

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
