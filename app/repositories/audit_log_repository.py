"""Query tabel `audit_logs` (lihat migrations/0002_audit_logs.sql)."""
from __future__ import annotations

from typing import Any

from app.core.constants import Tables
from app.core.pagination import Pagination
from app.db.client import get_supabase
from app.repositories.base import first_or_none, run


def find_all(pagination: Pagination | None = None) -> tuple[list[dict], int]:
    query = get_supabase().table(Tables.AUDIT_LOGS).select("*", count="exact").order("created_at", desc=True)
    if pagination:
        query = query.range(pagination.start, pagination.end)
    response = run(query)
    return response.data or [], response.count or 0


def find_by_id(log_id: int) -> dict | None:
    response = run(get_supabase().table(Tables.AUDIT_LOGS).select("*").eq("id", log_id))
    return first_or_none(response)


def create(payload: dict[str, Any]) -> dict | None:
    response = run(get_supabase().table(Tables.AUDIT_LOGS).insert(payload))
    return first_or_none(response)
