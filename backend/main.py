"""Compatibility entry point for the active CineList FastAPI application.

Use ``uvicorn app.main:app`` as the canonical command. This alias ensures that
older commands targeting ``backend.main:app`` still run the same PostgreSQL-
backed application instead of the retired Supabase implementation.
"""
from app.main import app, create_app

__all__ = ["app", "create_app"]
