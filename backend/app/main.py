import logging
import os

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api.deps import get_current_user
from app.core.security import SupabaseUser
from app.core.config import settings
from app.api.routes import activities, reviews, dashboard, roadmaps, admin, feedback, internal, prefs, tests, syllabus
from app.services import analytics

# So Render's log stream carries tracebacks even with Sentry off — logging is
# the floor, Sentry is the upgrade.
logging.basicConfig(level=logging.INFO)

# Gated on SENTRY_DSN so this is a safe no-op until the founder sets it (Render
# env). No custom @app.exception_handler(Exception): sentry-sdk's FastAPI
# integration captures unhandled exceptions itself, and a custom handler risks
# swallowing them before Sentry sees the exception.
if settings.SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT,
        release=os.environ.get("RENDER_GIT_COMMIT"),
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        send_default_pii=False,  # pseudonymous only — matches analytics.js
    )

app = FastAPI(title="RetainHQ API", version="1.0.0")


@app.on_event("shutdown")
async def _flush_analytics():
    # Flush any buffered server-side PostHog events before the worker exits.
    analytics.shutdown()

# Env-driven CORS allow-list (comma-separated in CORS_ORIGINS env var)
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

app.include_router(activities.router, prefix="/api/activities", tags=["activities"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["reviews"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(roadmaps.router, prefix="/api/roadmaps", tags=["roadmaps"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["feedback"])
app.include_router(internal.router, prefix="/api/internal", tags=["internal"])
app.include_router(prefs.router, prefix="/api/prefs", tags=["prefs"])
app.include_router(tests.router, prefix="/api/tests", tags=["tests"])
app.include_router(syllabus.router, prefix="/api/syllabus", tags=["syllabus"])

@app.get("/me")
async def get_me(current_user: SupabaseUser = Depends(get_current_user)):
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "message": "You are successfully authenticated through Supabase via FastAPI!"
    }
