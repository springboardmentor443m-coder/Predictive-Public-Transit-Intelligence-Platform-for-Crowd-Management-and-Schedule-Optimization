from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.database import Base, engine
from app.models.station import Station
from app.routes.station import router as station_router
from app.routes.analytics import router as analytics_router

app = FastAPI(
    title="MetroFlow – AI Public Transit Intelligent Platform",
    description="AI-powered Bangalore Metro Crowd Management, Schedule Optimization & Live Analytics",
    version="2.0.0",
)

# Allow Next.js dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


app.include_router(station_router)
app.include_router(analytics_router)


@app.get("/")
def root():
    return {
        "message": "MetroFlow AI Platform is running",
        "version": "2.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/database-test")
def database_test():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT current_database();"))
            database_name = result.fetchone()[0]
        return {
            "status": "success",
            "message": "Database connected successfully",
            "database": database_name,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}