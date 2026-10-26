"""PostgreSQL queries for the movie catalog."""
from __future__ import annotations

from typing import Any

from app.core.pagination import Pagination
from app.db.executor import execute_returning, fetch_all_with_count, fetch_one


def find_all(
    search: str | None = None,
    genre: str | None = None,
    pagination: Pagination | None = None,
) -> tuple[list[dict], int]:
    clauses: list[str] = []
    params: dict[str, Any] = {}
    if search:
        clauses.append("title ILIKE :search")
        params["search"] = f"%{search}%"
    if genre:
        clauses.append("genre ILIKE :genre")
        params["genre"] = f"%{genre}%"
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    limit_clause = ""
    if pagination:
        params.update(limit=pagination.limit, offset=pagination.offset)
        limit_clause = " LIMIT :limit OFFSET :offset"
    return fetch_all_with_count(
        f"SELECT * FROM movies{where} ORDER BY id ASC{limit_clause}",
        f"SELECT COUNT(*) FROM movies{where}",
        params,
    )


def find_by_id(movie_id: int) -> dict | None:
    return fetch_one("SELECT * FROM movies WHERE id = :movie_id", {"movie_id": movie_id})


def create(payload: dict[str, Any]) -> dict | None:
    return execute_returning(
        """INSERT INTO movies
           (title, release_year, genre, director, overview, poster_url, rating)
           VALUES (:title, :release_year, :genre, :director, :overview, :poster_url, :rating)
           RETURNING *""",
        payload,
    )


def update(movie_id: int, payload: dict[str, Any]) -> dict | None:
    allowed = {"title", "release_year", "genre", "director", "overview", "poster_url", "rating"}
    values = {key: value for key, value in payload.items() if key in allowed}
    if not values:
        return find_by_id(movie_id)
    assignments = ", ".join(f"{key} = :{key}" for key in values)
    values["movie_id"] = movie_id
    return execute_returning(
        f"UPDATE movies SET {assignments} WHERE id = :movie_id RETURNING *",
        values,
    )


def delete(movie_id: int) -> dict | None:
    return execute_returning("DELETE FROM movies WHERE id = :movie_id RETURNING *", {"movie_id": movie_id})
