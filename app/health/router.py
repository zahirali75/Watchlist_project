"""Endpoint cek status API."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from app.core.config import Settings, get_settings
from app.health import service

router = APIRouter(tags=["Health Check"])


@router.get("/", include_in_schema=False)
def redirect_to_docs(settings: Settings = Depends(get_settings)):
    # Production: /docs dimatikan, jadi jangan redirect ke sana (akan 404).
    if settings.is_production:
        return {"success": True, "message": f"{settings.APP_NAME} berjalan", "data": {"app": settings.APP_NAME}}
    return RedirectResponse(url="/docs")


@router.get("/health")
def health_check(settings: Settings = Depends(get_settings)) -> dict:
    """Liveness: aplikasi hidup dan konfigurasi valid (tidak menyentuh database)."""
    return {
        "success": True,
        "message": f"Selamat datang di {settings.APP_NAME}! 🎬",
        "data": {
            "app": settings.APP_NAME,
            "env": settings.APP_ENV,
            "version": "2.0.0",
            "docs": None if settings.is_production else "/docs",
        },
    }


@router.get("/health/db")
def readiness_check() -> dict:
    """Readiness (PENAMBAHAN BARU): memeriksa koneksi database dengan SELECT 1."""
    service.check_database()
    return {"success": True, "message": "Database terhubung", "data": {"database": "ok"}}
