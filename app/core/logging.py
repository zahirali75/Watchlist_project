"""Konfigurasi logging terpusat.

Setiap modul memakai logger bernama `app.<fitur>` (app.auth, app.movies,
app.watchlists, app.users, app.audit_logs, app.db, app.core), sehingga di log
langsung terlihat fitur mana yang bermasalah. Jangan pernah mencatat password,
token, atau secret.
"""
from __future__ import annotations

import logging

LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def setup_logging(level: int = logging.INFO) -> None:
    """Dipanggil sekali saat aplikasi dibuat. Aman dipanggil berulang (tes)."""
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=level, format=LOG_FORMAT)
    logging.getLogger("app").setLevel(level)


def get_logger(feature: str) -> logging.Logger:
    """get_logger("auth") -> logger `app.auth`."""
    return logging.getLogger(f"app.{feature}")
