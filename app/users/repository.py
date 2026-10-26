"""PostgreSQL queries for users. Password hashes are only returned for login."""
from __future__ import annotations

from typing import Any

from app.core.pagination import Pagination
from app.db.executor import execute_returning, fetch_all_with_count, fetch_one

PUBLIC_COLUMNS = "id, name, email, role, created_at"


def find_all(pagination: Pagination | None = None) -> tuple[list[dict], int]:
    params: dict[str, Any] = {}
    limit_clause = ""
    if pagination:
        params.update(limit=pagination.limit, offset=pagination.offset)
        limit_clause = " LIMIT :limit OFFSET :offset"
    return fetch_all_with_count(
        f"SELECT {PUBLIC_COLUMNS} FROM users ORDER BY created_at DESC{limit_clause}",
        "SELECT COUNT(*) FROM users",
        params,
    )


def find_by_id(user_id: str) -> dict | None:
    return fetch_one(f"SELECT {PUBLIC_COLUMNS} FROM users WHERE id = :user_id", {"user_id": user_id})


def find_identity(user_id: str) -> dict | None:
    """Hanya id + role terkini; dipakai untuk memvalidasi token di setiap request."""
    return fetch_one("SELECT id, role FROM users WHERE id = :user_id", {"user_id": user_id})


def find_by_email(email: str) -> dict | None:
    return fetch_one(f"SELECT {PUBLIC_COLUMNS} FROM users WHERE lower(email) = lower(:email)", {"email": email})


def find_auth_by_email(email: str) -> dict | None:
    return fetch_one(
        "SELECT id, email, name, role, password_hash FROM users WHERE lower(email) = lower(:email)",
        {"email": email},
    )


def create(payload: dict[str, Any]) -> dict | None:
    return execute_returning(
        """INSERT INTO users (name, email, password_hash, role)
           VALUES (:name, lower(:email), :password_hash, :role)
           RETURNING id, name, email, role, created_at""",
        payload,
    )


def update_password_hash(user_id: str, password_hash: str) -> bool:
    row = execute_returning(
        "UPDATE users SET password_hash = :password_hash WHERE id = :user_id RETURNING id",
        {"user_id": user_id, "password_hash": password_hash},
    )
    return row is not None
