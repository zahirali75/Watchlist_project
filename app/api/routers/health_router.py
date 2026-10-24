"""Endpoint cek status API."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from app.core.config import Settings, get_settings

router = APIRouter(tags=["Health Check"])


@router.get("/", include_in_schema=False)
def redirect_to_docs() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@router.get("/health", tags=["Health Check"])
def health_check(settings: Settings = Depends(get_settings)) -> dict:
    return {
        "success": True,
        "message": f"Selamat datang di {settings.APP_NAME}! 🎬",
        "data": {
            "app": settings.APP_NAME,
            "env": settings.APP_ENV,
            "version": "2.0.0",
            "docs": "/docs",
        },
    }
