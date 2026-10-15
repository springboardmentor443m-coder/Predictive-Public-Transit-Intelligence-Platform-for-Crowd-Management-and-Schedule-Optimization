from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import network, schedule, incidents, integrations  # integrations import cheyandi

app = FastAPI(
    title="MetroFlow Intelligence Platform",
    description="Real-Time Seoul Metro Flow, Turnstile Telemetry & Third-Party Integrations",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core Routers
app.include_router(network.router)
app.include_router(schedule.router)
app.include_router(incidents.router)
app.include_router(integrations.router)  # <--- Integrations router add chesam

@app.get("/api/health")
def health():
    return {"status": "ONLINE", "transit_network": "ACTIVE"}