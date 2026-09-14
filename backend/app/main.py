from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import Base, engine, SessionLocal
from app.models.user import User  # noqa
from app.models.transit import Station, Ridership, Schedule, Alert  # noqa
from app.api.routes import auth, crowd, scheduling, prediction, alerts, analytics
from app.core.security import get_password_hash

app = FastAPI(title="MetroFlow AI Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def ensure_admin():
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            db.add(User(username="admin", full_name="Metro Admin",
                        hashed_password=get_password_hash("admin123"), role="admin"))
            db.commit()
        if not db.query(User).filter(User.username == "operator").first():
            db.add(User(username="operator", full_name="Station Operator",
                        hashed_password=get_password_hash("operator123"), role="operator"))
            db.commit()
    finally:
        db.close()


app.include_router(auth.router)
app.include_router(crowd.router)
app.include_router(scheduling.router)
app.include_router(prediction.router)
app.include_router(alerts.router, prefix="")
app.include_router(analytics.router)


@app.get("/")
def root():
    return {"service": "MetroFlow AI", "status": "ok", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}
