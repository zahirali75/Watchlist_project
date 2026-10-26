"""PostgreSQL queries for audit logs (migration 0002)."""
from __future__ import annotations

from typing import Any

from app.core.pagination import Pagination
from app.db.executor import execute_returning, fetch_all_with_count, fetch_one


def find_all(pagination: Pagination | None = None) -> tuple[list[dict], int]:
    params: dict[str, Any] = {}
    limit_clause = ""
    if pagination:
        params.update(limit=pagination.limit, offset=pagination.offset)
        limit_clause = " LIMIT :limit OFFSET :offset"
    return fetch_all_with_count(
        f"SELECT * FROM audit_logs ORDER BY created_at DESC{limit_clause}",
        "SELECT COUNT(*) FROM audit_logs",
        params,
    )


def find_by_id(log_id: int) -> dict | None:
    return fetch_one("SELECT * FROM audit_logs WHERE id = :log_id", {"log_id": log_id})


def create(payload: dict[str, Any]) -> dict | None:
    return execute_returning(
        """INSERT INTO audit_logs (context, type, created_by)
           VALUES (:context, :type, :created_by) RETURNING *""",
        payload,
    )
