"""PostgreSQL queries for user watchlists."""
from __future__ import annotations

from typing import Any

from app.core.pagination import Pagination
from app.db.executor import execute_returning, fetch_all_with_count, fetch_one


def find_all_by_user(
    user_id: str,
    status: str | None = None,
    pagination: Pagination | None = None,
) -> tuple[list[dict], int]:
    clauses = ["w.user_id = :user_id"]
    params: dict[str, Any] = {"user_id": user_id}
    if status:
        clauses.append("w.status = :status")
        params["status"] = status
    where = " WHERE " + " AND ".join(clauses)
    limit_clause = ""
    if pagination:
        params.update(limit=pagination.limit, offset=pagination.offset)
        limit_clause = " LIMIT :limit OFFSET :offset"
    return fetch_all_with_count(
        f"SELECT w.*, row_to_json(m) AS movies FROM watchlists w JOIN movies m ON m.id = w.movie_id{where} ORDER BY w.created_at DESC{limit_clause}",
        f"SELECT COUNT(*) FROM watchlists w{where}",
        params,
    )


def find_by_id(watchlist_id: int) -> dict | None:
    return fetch_one("SELECT * FROM watchlists WHERE id = :watchlist_id", {"watchlist_id": watchlist_id})


def find_by_user_and_movie(user_id: str, movie_id: int) -> dict | None:
    return fetch_one(
        "SELECT * FROM watchlists WHERE user_id = :user_id AND movie_id = :movie_id",
        {"user_id": user_id, "movie_id": movie_id},
    )


def create(payload: dict[str, Any]) -> dict | None:
    return execute_returning(
        """INSERT INTO watchlists (user_id, movie_id, status, notes)
           VALUES (:user_id, :movie_id, :status, :notes) RETURNING *""",
        payload,
    )


def update(watchlist_id: int, payload: dict[str, Any]) -> dict | None:
    allowed = {"status", "notes"}
    values = {key: value for key, value in payload.items() if key in allowed}
    if not values:
        return find_by_id(watchlist_id)
    assignments = ", ".join(f"{key} = :{key}" for key in values)
    values["watchlist_id"] = watchlist_id
    return execute_returning(
        f"UPDATE watchlists SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = :watchlist_id RETURNING *",
        values,
    )


def delete(watchlist_id: int) -> dict | None:
    return execute_returning("DELETE FROM watchlists WHERE id = :watchlist_id RETURNING *", {"watchlist_id": watchlist_id})


def count_by_status(user_id: str, status: str | None = None) -> int:
    params: dict[str, Any] = {"user_id": user_id}
    sql = "SELECT COUNT(*) FROM watchlists WHERE user_id = :user_id"
    if status:
        sql += " AND status = :status"
        params["status"] = status
    row = fetch_one(f"SELECT ({sql})::bigint AS count", params)
    return int(row["count"]) if row else 0
