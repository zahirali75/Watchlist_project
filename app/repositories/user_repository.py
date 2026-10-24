"""Query tabel `users`.

Aturan penting: `password_hash` TIDAK PERNAH ikut di daftar kolom publik.
Hanya find_auth_by_email() yang boleh menariknya, khusus untuk login.
"""
from __future__ import annotations

from typing import Any

from app.core.constants import Tables
from app.core.pagination import Pagination
from app.db.client import get_supabase
from app.repositories.base import first_or_none, run

PUBLIC_COLUMNS = "id, name, email, role, created_at"


def find_all(pagination: Pagination | None = None) -> tuple[list[dict], int]:
    query = get_supabase().table(Tables.USERS).select(PUBLIC_COLUMNS, count="exact").order("created_at", desc=True)
    if pagination:
        query = query.range(pagination.start, pagination.end)
    response = run(query)
    return response.data or [], response.count or 0


def find_by_id(user_id: str) -> dict | None:
    response = run(get_supabase().table(Tables.USERS).select(PUBLIC_COLUMNS).eq("id", user_id))
    return first_or_none(response)


def find_by_email(email: str) -> dict | None:
    response = run(get_supabase().table(Tables.USERS).select(PUBLIC_COLUMNS).eq("email", email))
    return first_or_none(response)


def find_auth_by_email(email: str) -> dict | None:
    """KHUSUS login: ikut menarik password_hash."""
    response = run(get_supabase().table(Tables.USERS).select("id, email, name, role, password_hash").eq("email", email))
    return first_or_none(response)


def create(payload: dict[str, Any]) -> dict | None:
    response = run(get_supabase().table(Tables.USERS).insert(payload))
    return first_or_none(response)
