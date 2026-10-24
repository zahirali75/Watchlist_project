"""Query tabel `watchlists`."""
from __future__ import annotations

from typing import Any

from app.core.constants import Tables
from app.core.pagination import Pagination
from app.db.client import get_supabase
from app.repositories.base import first_or_none, run

JOIN_MOVIE = "*, movies(*)"


def find_all_by_user(
    user_id: str,
    status: str | None = None,
    pagination: Pagination | None = None,
) -> tuple[list[dict], int]:
    query = (
        get_supabase()
        .table(Tables.WATCHLISTS)
        .select(JOIN_MOVIE, count="exact")
        .eq("user_id", user_id)
    )
    if status:
        query = query.eq("status", status)
    query = query.order("created_at", desc=True)
    if pagination:
        query = query.range(pagination.start, pagination.end)

    response = run(query)
    return response.data or [], response.count or 0


def find_by_id(watchlist_id: int) -> dict | None:
    response = run(get_supabase().table(Tables.WATCHLISTS).select("*").eq("id", watchlist_id))
    return first_or_none(response)


def find_by_user_and_movie(user_id: str, movie_id: int) -> dict | None:
    response = run(
        get_supabase()
        .table(Tables.WATCHLISTS)
        .select("*")
        .eq("user_id", user_id)
        .eq("movie_id", movie_id)
    )
    return first_or_none(response)


def create(payload: dict[str, Any]) -> dict | None:
    response = run(get_supabase().table(Tables.WATCHLISTS).insert(payload))
    return first_or_none(response)


def update(watchlist_id: int, payload: dict[str, Any]) -> dict | None:
    response = run(get_supabase().table(Tables.WATCHLISTS).update(payload).eq("id", watchlist_id))
    return first_or_none(response)


def delete(watchlist_id: int) -> dict | None:
    response = run(get_supabase().table(Tables.WATCHLISTS).delete().eq("id", watchlist_id))
    return first_or_none(response)


def count_by_status(user_id: str, status: str | None = None) -> int:
    """Hitung baris di database (head=True -> tidak menarik datanya)."""
    query = get_supabase().table(Tables.WATCHLISTS).select("id", count="exact", head=True).eq("user_id", user_id)
    if status:
        query = query.eq("status", status)
    response = run(query)
    return response.count or 0
