from fastapi import FastAPI
from sqlalchemy import text
from app.database import Base, engine
from app.models.station import Station
from app.routes.station import router as station_router

app = FastAPI(
    title="MetroFlow API",
    description="AI-powered Metro Crowd Management and Schedule Optimization API",
    version="1.0.0",
)


@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)

app.include_router(station_router)

@app.get("/")
def root():
    return {
        "message": "MetroFlow API is running",
        "status": "success",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }


@app.get("/database-test")
def database_test():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT current_database();"))
            database_name = result.fetchone()[0]

        return {
            "status": "success",
            "message": "Database connected successfully using SQLAlchemy",
            "database": database_name,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }