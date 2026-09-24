from fastapi import FastAPI

from app.database import Base, engine
from app.models import user
from app.routers import health, auth

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="AI MetroFlow API",
    description="Backend API for the AI-powered metro crowd management and scheduling platform.",
    version="1.0.0"
)


app.include_router(health.router)
app.include_router(auth.router)


@app.get("/")
def root():
    return {
        "message": "Welcome to AI MetroFlow",
        "status": "Backend is running"
    }