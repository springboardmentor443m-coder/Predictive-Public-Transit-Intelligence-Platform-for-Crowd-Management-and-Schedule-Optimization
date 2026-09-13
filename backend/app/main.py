import asyncio
import logging
import os
from contextlib import asynccontextmanager

import socketio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

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
    broadcast_task = None
    if os.environ.get("METROFLOW_ENABLE_REALTIME", "1") not in ("0", "", "false", "False"):
        broadcast_task = asyncio.create_task(broadcast_loop())
        logger.info("MetroFlow startup complete; realtime broadcast started")
    else:
        logger.info("MetroFlow startup complete; realtime broadcast disabled")
    yield
    logger.info("MetroFlow shutting down")
    if broadcast_task is not None:
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


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error("Database error on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=503,
        content={"detail": "Database is temporarily unavailable. Please retry shortly."},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again."},
    )


app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"app": "MetroFlow", "api": "/api/v1/docs", "status": "running"}


socket_app = socketio.ASGIApp(sio, other_asgi_app=app)
