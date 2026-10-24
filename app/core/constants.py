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


class AuditType(str, Enum):
    MOVIE_CREATE = "MOVIE_CREATE"
    MOVIE_UPDATE = "MOVIE_UPDATE"
    MOVIE_DELETE = "MOVIE_DELETE"
    USER_REGISTER = "USER_REGISTER"
