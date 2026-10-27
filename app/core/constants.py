"""Nilai tetap domain + nama tabel (satu sumber kebenaran)."""
from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    user = "user"
    admin = "admin"


class Tables:
    USERS = "users"
    MOVIES = "movies"
    WATCHLISTS = "watchlists"
    AUDIT_LOGS = "audit_logs"
    REFRESH_TOKENS = "refresh_tokens"


class AuditType(str, Enum):
    MOVIE_CREATE = "MOVIE_CREATE"
    MOVIE_UPDATE = "MOVIE_UPDATE"
    MOVIE_DELETE = "MOVIE_DELETE"
    USER_REGISTER = "USER_REGISTER"
    USER_PROFILE_UPDATE = "USER_PROFILE_UPDATE"
    # Ganti password TIDAK dicatat isinya di sini: password tidak pernah masuk log.
    # Yang dicatat hanya peristiwanya (lihat app/auth/service.py).
    USER_CHANGE_PASSWORD = "USER_CHANGE_PASSWORD"
    USER_PASSWORD_RESET = "USER_PASSWORD_RESET"
