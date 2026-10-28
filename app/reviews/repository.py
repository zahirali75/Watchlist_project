"""PostgreSQL queries for reviews.

Semua query mengambil `user_name` (JOIN users) dan `movie_title` (JOIN movies)
supaya frontend tidak perlu memanggil endpoint lain hanya untuk menampilkan nama
penulis atau judul film. Kolom `is_hidden` ikut dikirim; penyaringan berdasarkan
hak akses dilakukan di service, bukan di sini.
"""
from __future__ import annotations

from typing import Any

from app.core.pagination import Pagination
from app.db.executor import execute_returning, fetch_all_with_count, fetch_one

COLUMNS = (
    "r.id, r.user_id, r.movie_id, r.rating, r.content, r.is_hidden, "
    "r.created_at, r.updated_at, u.name AS user_name, m.title AS movie_title"
)
JOINS = "FROM reviews r JOIN users u ON u.id = r.user_id JOIN movies m ON m.id = r.movie_id"


def find_by_movie(movie_id: int, pagination: Pagination | None = None) -> tuple[list[dict], int]:
    """Ulasan publik sebuah film (yang disembunyikan admin tidak ikut)."""
    where = " WHERE r.movie_id = :movie_id AND r.is_hidden = FALSE"
    params: dict[str, Any] = {"movie_id": movie_id}
    limit_clause = ""
    if pagination:
        params.update(limit=pagination.limit, offset=pagination.offset)
        limit_clause = " LIMIT :limit OFFSET :offset"
    return fetch_all_with_count(
        f"SELECT {COLUMNS} {JOINS}{where} ORDER BY r.created_at DESC{limit_clause}",
        f"SELECT COUNT(*) {JOINS}{where}",
        params,
    )


def find_all_by_user(user_id: str, pagination: Pagination | None = None) -> tuple[list[dict], int]:
    """Ulasan milik sendiri - termasuk yang disembunyikan, supaya pemiliknya tahu."""
    where = " WHERE r.user_id = :user_id"
    params: dict[str, Any] = {"user_id": user_id}
    limit_clause = ""
    if pagination:
        params.update(limit=pagination.limit, offset=pagination.offset)
        limit_clause = " LIMIT :limit OFFSET :offset"
    return fetch_all_with_count(
        f"SELECT {COLUMNS} {JOINS}{where} ORDER BY r.created_at DESC{limit_clause}",
        f"SELECT COUNT(*) {JOINS}{where}",
        params,
    )


def find_all_for_moderation(pagination: Pagination | None = None) -> tuple[list[dict], int]:
    """Seluruh ulasan untuk admin (termasuk yang sedang disembunyikan)."""
    params: dict[str, Any] = {}
    limit_clause = ""
    if pagination:
        params.update(limit=pagination.limit, offset=pagination.offset)
        limit_clause = " LIMIT :limit OFFSET :offset"
    return fetch_all_with_count(
        f"SELECT {COLUMNS} {JOINS} ORDER BY r.created_at DESC{limit_clause}",
        f"SELECT COUNT(*) {JOINS}",
        params,
    )


def find_by_id(review_id: int) -> dict | None:
    return fetch_one(f"SELECT {COLUMNS} {JOINS} WHERE r.id = :review_id", {"review_id": review_id})


def find_by_user_and_movie(user_id: str, movie_id: int) -> dict | None:
    return fetch_one(
        f"SELECT {COLUMNS} {JOINS} WHERE r.user_id = :user_id AND r.movie_id = :movie_id",
        {"user_id": user_id, "movie_id": movie_id},
    )


def create(payload: dict[str, Any]) -> dict | None:
    return execute_returning(
        """INSERT INTO reviews (user_id, movie_id, rating, content)
           VALUES (:user_id, :movie_id, :rating, :content)
           RETURNING id""",
        payload,
    )


def update(review_id: int, payload: dict[str, Any]) -> dict | None:
    allowed = {"rating", "content"}
    values = {key: value for key, value in payload.items() if key in allowed}
    if not values:
        return find_by_id(review_id)
    assignments = ", ".join(f"{key} = :{key}" for key in values)
    values["review_id"] = review_id
    return execute_returning(
        f"UPDATE reviews SET {assignments}, updated_at = CURRENT_TIMESTAMP "
        f"WHERE id = :review_id RETURNING id",
        values,
    )


def set_hidden(review_id: int, is_hidden: bool) -> dict | None:
    return execute_returning(
        "UPDATE reviews SET is_hidden = :is_hidden, updated_at = CURRENT_TIMESTAMP "
        "WHERE id = :review_id RETURNING id",
        {"review_id": review_id, "is_hidden": is_hidden},
    )


def delete(review_id: int) -> dict | None:
    return execute_returning("DELETE FROM reviews WHERE id = :review_id RETURNING id", {"review_id": review_id})
