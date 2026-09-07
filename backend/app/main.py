import json
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import async_engine, Base
from app.api.v1.api_router import api_router
from app.services.crowd_service import crowd_service
from app.services.alert_service import alert_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("metroflow.main")


class WebSocketConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)


ws_manager = WebSocketConnectionManager()


async def background_telemetry_broadcaster():
    """Continuously broadcasts live crowd density, train telemetry, and alerts to UI."""
    while True:
        try:
            summary = await crowd_service.get_crowd_summary()
            alerts = await alert_service.get_active_alerts()
            
            payload = {
                "event": "TELEMETRY_UPDATE",
                "summary": summary.model_dump(mode="json"),
                "alerts_count": len([a for a in alerts if not a.is_resolved]),
            }
            await ws_manager.broadcast(payload)
        except Exception as e:
            logger.error(f"Error in telemetry broadcast task: {e}")

        await asyncio.sleep(3.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Initializing MetroFlow backend services...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Start background WebSocket broadcaster
    broadcast_task = asyncio.create_task(background_telemetry_broadcaster())
    
    yield
    
    # Shutdown actions
    broadcast_task.cancel()
    logger.info("MetroFlow backend shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "system": settings.PROJECT_NAME,
        "status": "OPERATIONAL",
        "version": "1.0.0",
        "docs_url": "/docs",
    }


@app.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection open & listen for client messages if any
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
