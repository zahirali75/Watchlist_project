"""Aturan bisnis modul users."""
from __future__ import annotations

from app.core.exceptions import NotFoundError
from app.core.pagination import Pagination
from app.repositories import user_repository as repo


def get_all_users(pagination: Pagination | None = None) -> dict:
    items, total = repo.find_all(pagination)
    return {"items": items, "total": total}


def find_user_by_id(user_id: str) -> dict:
    user = repo.find_by_id(user_id)
    if not user:
        raise NotFoundError(f"User {user_id} tidak ditemukan")
    return user
