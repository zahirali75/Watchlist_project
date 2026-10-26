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

from app.core.config import Settings, get_settings
from app.core.error_handlers import register_exception_handlers
from app.core.logging import setup_logging
from app.audit_logs.router import router as audit_logs_router
from app.auth.router import router as auth_router
from app.db.session import dispose_engine
from app.health.router import router as health_router
from app.movies.router import router as movies_router
from app.users.router import router as users_router
from app.watchlists.router import router as watchlists_router

logger = logging.getLogger("app.core")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()  # memicu validasi env; gagal = app tidak start
    logger.info("%s (%s) siap di port %s", settings.APP_NAME, settings.APP_ENV, settings.APP_PORT)
    yield
    dispose_engine()
    logger.info("Server dimatikan")


def create_app() -> FastAPI:
    setup_logging()
    settings: Settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version="2.0.0",
        lifespan=lifespan,
        # Dokumentasi interaktif hanya untuk development/test.
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url=None if settings.is_production else "/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    for router in (
        health_router,
        auth_router,
        movies_router,
        watchlists_router,
        users_router,
        audit_logs_router,
    ):
        app.include_router(router)

    register_exception_handlers(app)
    return app


app = create_app()
