"""Compatibility exports for direct PostgreSQL access.

The old implementation created a Supabase REST client. The application now
uses the PostgreSQL DSN configured by DATABASE_URL and SQLAlchemy Core. Keeping
these exports preserves the historical module path without retaining a second
or inconsistent database implementation.
"""
from app.db.session import get_connection, get_engine

__all__ = ["get_connection", "get_engine"]
