from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api.deps import get_current_user
from app.core.security import SupabaseUser
from app.api.routes import activities, reviews, dashboard, roadmaps, admin, feedback

app = FastAPI(title="RetainHQ API", version="1.0.0")

# Configure CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # Add Vercel domain later
]

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

@app.get("/me")
async def get_me(current_user: SupabaseUser = Depends(get_current_user)):
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "message": "You are successfully authenticated through Supabase via FastAPI!"
    }
