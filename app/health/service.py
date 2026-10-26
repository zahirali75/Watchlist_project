"""Logika cek kesiapan (readiness)."""
from __future__ import annotations

from app.core.exceptions import UpstreamError
from app.health import repository as repo


def check_database() -> None:
    """Lolos bila database menjawab; selain itu 502 (error koneksi sudah diterjemahkan executor)."""
    if not repo.ping():
        raise UpstreamError("Database tidak merespons")
