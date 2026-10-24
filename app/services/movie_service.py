"""Aturan bisnis modul movies."""
from __future__ import annotations

from app.core.constants import AuditType
from app.core.exceptions import NotFoundError
from app.core.pagination import Pagination
from app.repositories import movie_repository as repo
from app.schemas.audit_log_schema import AuditLogCreate
from app.schemas.movie_schema import MovieCreate, MovieUpdate
from app.services import audit_log_service


def get_movies(
    search: str | None = None,
    genre: str | None = None,
    pagination: Pagination | None = None,
) -> dict:
    items, total = repo.find_all(search=search, genre=genre, pagination=pagination)
    return {"items": items, "total": total}


def find_movie_by_id(movie_id: int) -> dict:
    movie = repo.find_by_id(movie_id)
    if not movie:
        raise NotFoundError(f"Film dengan id {movie_id} tidak ditemukan")
    return movie


def create_movie(data: MovieCreate, admin_id: str | None = None) -> dict:
    movie = repo.create(data.model_dump())
    if not movie:
        raise NotFoundError("Gagal menyimpan film ke database")

    audit_log_service.create_audit_log(
        AuditLogCreate(
            context=f"Admin (ID: {admin_id}) menambah film (ID: {movie.get('id')}): {movie.get('title')}",
            type=AuditType.MOVIE_CREATE.value,
        ),
        actor_id=admin_id,
    )
    return movie


def update_movie(movie_id: int, data: MovieUpdate, admin_id: str | None = None) -> dict:
    old_movie = find_movie_by_id(movie_id)  # 404 kalau tidak ada

    updated = repo.update(movie_id, data.model_dump())
    if not updated:
        raise NotFoundError(f"Film {movie_id} gagal diupdate")

    audit_log_service.create_audit_log(
        AuditLogCreate(
            context=(
                f"Admin (ID: {admin_id}) mengubah film (ID: {movie_id}). "
                f"Sebelum: {old_movie.get('title')} ({old_movie.get('release_year')}) | "
                f"Sesudah: {updated.get('title')} ({updated.get('release_year')})"
            ),
            type=AuditType.MOVIE_UPDATE.value,
        ),
        actor_id=admin_id,
    )
    return updated


def delete_movie(movie_id: int, admin_id: str | None = None) -> dict:
    old_movie = find_movie_by_id(movie_id)

    deleted = repo.delete(movie_id)
    if not deleted:
        raise NotFoundError(f"Film {movie_id} gagal dihapus")

    audit_log_service.create_audit_log(
        AuditLogCreate(
            context=f"Admin (ID: {admin_id}) menghapus film (ID: {movie_id}): {old_movie.get('title')}",
            type=AuditType.MOVIE_DELETE.value,
        ),
        actor_id=admin_id,
    )
    return deleted
