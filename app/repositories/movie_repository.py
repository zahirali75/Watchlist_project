"""Query tabel `movies`. Tidak ada aturan bisnis di lapisan ini."""
from __future__ import annotations

from typing import Any

from app.core.constants import Tables
from app.core.pagination import Pagination
from app.db.client import get_supabase
from app.repositories.base import first_or_none, run


def find_all(
    search: str | None = None,
    genre: str | None = None,
    pagination: Pagination | None = None,
) -> tuple[list[dict], int]:
    """Kembalikan (daftar film, total baris). count="exact" dari PostgREST."""
    query = get_supabase().table(Tables.MOVIES).select("*", count="exact")
    if search:
        query = query.ilike("title", f"%{search}%")
    if genre:
        query = query.ilike("genre", f"%{genre}%")
    query = query.order("id", desc=False)
    if pagination:
        query = query.range(pagination.start, pagination.end)

    response = run(query)
    return response.data or [], response.count or 0


def find_by_id(movie_id: int) -> dict | None:
    response = run(get_supabase().table(Tables.MOVIES).select("*").eq("id", movie_id))
    return first_or_none(response)


def create(payload: dict[str, Any]) -> dict | None:
    response = run(get_supabase().table(Tables.MOVIES).insert(payload))
    return first_or_none(response)


def update(movie_id: int, payload: dict[str, Any]) -> dict | None:
    response = run(get_supabase().table(Tables.MOVIES).update(payload).eq("id", movie_id))
    return first_or_none(response)


def delete(movie_id: int) -> dict | None:
    response = run(get_supabase().table(Tables.MOVIES).delete().eq("id", movie_id))
    return first_or_none(response)
