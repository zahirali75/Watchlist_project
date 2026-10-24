"""Titik masuk aplikasi.

Dulu: 363 baris di backend/main.py berisi app + config + model + 12 endpoint.
Sekarang: berkas ini cuma merakit - bikin app, pasang middleware, daftarkan
router, dan pasang error handler global.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import (
    audit_log_router,
    auth_router,
    health_router,
    movie_router,
    user_router,
    watchlist_router,
)
from app.core.config import Settings, get_settings
from app.core.error_handlers import register_exception_handlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("cinelist")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()  # memicu validasi env; gagal = app tidak start
    logger.info("%s (%s) siap di port %s", settings.APP_NAME, settings.APP_ENV, settings.APP_PORT)
    yield
    logger.info("Server dimatikan")


def create_app() -> FastAPI:
    settings: Settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version="2.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router.router)
    app.include_router(auth_router.router)
    app.include_router(movie_router.router)
    app.include_router(watchlist_router.router)
    app.include_router(user_router.router)
    app.include_router(audit_log_router.router)

    register_exception_handlers(app)
    return app


app = create_app()
