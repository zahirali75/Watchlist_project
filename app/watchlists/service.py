"""Aturan bisnis modul watchlists (kepemilikan data ada di sini, bukan di router)."""
from __future__ import annotations

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.core.pagination import Pagination
from app.movies import service as movie_service
from app.watchlists import repository as repo
from app.watchlists.schemas import WatchlistCreate, WatchlistUpdate, WatchStatus


def _get_owned_item(watchlist_id: int, current_user_id: str) -> dict:
    """Ambil item + pastikan pemiliknya. Dipakai update & delete -> tidak duplikat."""
    item = repo.find_by_id(watchlist_id)
    if not item:
        raise NotFoundError(f"Watchlist item {watchlist_id} tidak ditemukan")
    if str(item["user_id"]) != str(current_user_id):
        raise ForbiddenError("Tidak diizinkan mengubah watchlist milik user lain")
    return item


def get_watchlist(
    user_id: str,
    current_user_id: str,
    status: WatchStatus | None = None,
    pagination: Pagination | None = None,
) -> dict:
    if str(current_user_id) != str(user_id):
        raise ForbiddenError("Tidak diizinkan mengakses watchlist user lain")

    items, total = repo.find_all_by_user(str(user_id), status=status.value if status else None, pagination=pagination)
    return {"items": items, "total": total}


def add_to_watchlist(data: WatchlistCreate, current_user_id: str) -> dict:
    # Film harus ada: movie_service melempar 404 bila tidak ditemukan
    movie_service.find_movie_by_id(data.movie_id)

    # Cegah duplikat sebelum menyentuh database (UNIQUE(user_id, movie_id) tetap jaga di DB)
    if repo.find_by_user_and_movie(str(current_user_id), data.movie_id):
        raise ConflictError(
            "Film ini sudah ada di watchlist kamu",
            meta={"movieId": data.movie_id},
        )

    item = repo.create(
        {
            "user_id": str(current_user_id),
            "movie_id": data.movie_id,
            "status": data.status.value,
            "notes": data.notes,
        }
    )
    if not item:
        raise NotFoundError("Gagal menambahkan film ke watchlist")
    return item


def update_watchlist_item(watchlist_id: int, data: WatchlistUpdate, current_user_id: str) -> dict:
    _get_owned_item(watchlist_id, current_user_id)

    # exclude_unset: hanya field yang dikirim. `notes: null` berarti menghapus catatan;
    # `status` tidak boleh null.
    payload = data.model_dump(exclude_unset=True)
    if payload.get("status", "") is None:
        raise BadRequestError("status tidak boleh null")
    if not payload:
        raise BadRequestError("Tidak ada data untuk diupdate")
    if "status" in payload and isinstance(payload["status"], WatchStatus):
        payload["status"] = payload["status"].value

    updated = repo.update(watchlist_id, payload)
    if not updated:
        raise NotFoundError(f"Watchlist item {watchlist_id} gagal diupdate")
    return updated


def delete_watchlist_item(watchlist_id: int, current_user_id: str) -> dict:
    _get_owned_item(watchlist_id, current_user_id)

    deleted = repo.delete(watchlist_id)
    if not deleted:
        raise NotFoundError(f"Watchlist item {watchlist_id} gagal dihapus")
    return deleted


def get_user_stats(user_id: str) -> dict:
    total = repo.count_by_status(user_id)
    watched = repo.count_by_status(user_id, WatchStatus.watched.value)
    watching = repo.count_by_status(user_id, WatchStatus.watching.value)
    want_to_watch = repo.count_by_status(user_id, WatchStatus.want_to_watch.value)
    return {
        "total": total,
        "watched": watched,
        "watching": watching,
        "wantToWatch": want_to_watch,
    }
