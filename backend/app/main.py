from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.network import router as network_router
from app.api.crowd import router as crowd_router
from app.api.schedule import router as schedule_router
from app.api.incidents import router as incidents_router

app = FastAPI(title="MetroFlow Transit Engine", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(network_router)
app.include_router(crowd_router)
app.include_router(schedule_router)
app.include_router(incidents_router)

@app.get("/api/health")
def health():
    return {"status": "ONLINE", "transit_network": "ACTIVE"}