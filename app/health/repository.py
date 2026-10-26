"""Query cek koneksi database."""
from __future__ import annotations

from app.db.executor import fetch_one


def ping() -> bool:
    row = fetch_one("SELECT 1 AS ok")
    return bool(row and row.get("ok") == 1)
