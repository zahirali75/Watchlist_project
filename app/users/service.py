"""Aturan bisnis modul users."""
from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError
from app.core.pagination import Pagination
from app.users import repository as repo


def get_all_users(pagination: Pagination | None = None) -> dict:
    items, total = repo.find_all(pagination)
    return {"items": items, "total": total}


def find_user_by_id(user_id: str) -> dict:
    try:
        uuid.UUID(str(user_id))
    except ValueError:
        # ID yang bukan UUID pasti tidak ada; jangan biarkan error tipe database bocor ke klien.
        raise NotFoundError(f"User {user_id} tidak ditemukan") from None
    user = repo.find_by_id(user_id)
    if not user:
        raise NotFoundError(f"User {user_id} tidak ditemukan")
    return user


# --- Dipakai fitur lain (mis. auth) lewat service, bukan langsung ke repository ---
def find_by_email(email: str) -> dict | None:
    return repo.find_by_email(email)


def find_auth_by_email(email: str) -> dict | None:
    """KHUSUS login: ikut menarik password_hash."""
    return repo.find_auth_by_email(email)


def find_auth_by_email_by_id(user_id: str) -> dict | None:
    """KHUSUS ganti password: versi find_auth_by_email yang mencari dengan ID."""
    return repo.find_auth_by_id(user_id)


def get_own_profile(user_id: str) -> dict:
    """Profil milik pengguna yang sedang login (endpoint /users/me)."""
    return find_user_by_id(user_id)


def update_own_profile(user_id: str, name: str) -> dict:
    updated = repo.update_profile(user_id, name)
    if not updated:
        raise NotFoundError(f"User {user_id} tidak ditemukan")
    return updated


def create_user(payload: dict) -> dict | None:
    return repo.create(payload)


def update_password_hash(user_id: str, password_hash: str) -> bool:
    return repo.update_password_hash(user_id, password_hash)


def find_identity(user_id: str) -> dict | None:
    """id + role terkini dari database (None bila user sudah tidak ada)."""
    return repo.find_identity(user_id)
