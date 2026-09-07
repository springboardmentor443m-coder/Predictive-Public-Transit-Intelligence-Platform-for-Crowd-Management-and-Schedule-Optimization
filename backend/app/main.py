import asyncio
import logging
from contextlib import asynccontextmanager

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.models import alert, ridership, schedule, station, train, user
from app.services import socketio_state
from app.services.realtime import broadcast_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("metroflow")


sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
)


@sio.event
async def connect(sid, environ):
    logger.info(f"Socket.IO client connected: {sid}")
    await sio.emit("connected", {"status": "ok"}, to=sid)


@sio.event
async def disconnect(sid):
    logger.info(f"Socket.IO client disconnected: {sid}")


socketio_state.set_sio(sio)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.ml.model_wrappers import load_models

    load_models()
    broadcast_task = asyncio.create_task(broadcast_loop())
    logger.info("MetroFlow startup complete; realtime broadcast started")
    yield
    logger.info("MetroFlow shutting down")
    broadcast_task.cancel()
    try:
        await broadcast_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"app": "MetroFlow", "api": "/api/v1/docs", "status": "running"}


socket_app = socketio.ASGIApp(sio, other_asgi_app=app)
