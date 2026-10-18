"""
MetroFlow: AI Platform for Metro Crowd Management and Scheduling
High-Performance FastAPI Central Application & WebSocket Live Server
"""

import asyncio
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from db.database import init_db
from simulator.live_engine import simulator
from routes.auth import router as auth_router
from routes.crowd import router as crowd_router
from routes.predictions import router as predictions_router
from routes.scheduling import router as scheduling_router
from routes.alerts import router as alerts_router
from routes.analytics import router as analytics_router

# Active WebSocket connections
active_connections: list[WebSocket] = []

async def simulation_loop():
    """Background task advancing NYC subway train coordinates and station crowd states every 3 seconds."""
    while True:
        try:
            simulator.tick_simulation()
            snapshot = simulator.get_full_snapshot()
            data_str = json.dumps(snapshot)
            
            # Broadcast to connected frontend clients
            disconnected = []
            for ws in active_connections:
                try:
                    await ws.send_text(data_str)
                except Exception:
                    disconnected.append(ws)

            for ws in disconnected:
                if ws in active_connections:
                    active_connections.remove(ws)
        except Exception as e:
            print(f"Error in simulation loop: {e}")
        
        await asyncio.sleep(3.0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database
    init_db()
    # Start background live simulation
    sim_task = asyncio.create_task(simulation_loop())
    yield
    # Cleanup
    sim_task.cancel()

app = FastAPI(
    title="MetroFlow Operations Platform",
    description="Enterprise Transit Operations, Crowd Prediction, and Automated Train Scheduling",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(auth_router)
app.include_router(crowd_router)
app.include_router(predictions_router)
app.include_router(scheduling_router)
app.include_router(alerts_router)
app.include_router(analytics_router)

@app.get("/")
def root():
    return {
        "platform": "MetroFlow Operations Platform",
        "status": "Operational",
        "version": "2.0.0",
        "active_sim": True,
        "transit_network": "New York Metropolitan Transit Authority (Simulated Operational Feeds)"
    }

@app.websocket("/ws/live")
async def websocket_live_feed(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        # Send initial immediate snapshot
        initial_snapshot = simulator.get_full_snapshot()
        await websocket.send_text(json.dumps(initial_snapshot))
        while True:
            # Keep socket alive and listen for optional client pings
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
    except Exception:
        if websocket in active_connections:
            active_connections.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
