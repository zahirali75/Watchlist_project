"""Aturan bisnis modul reviews (ulasan film).

Aturan akses yang ditegakkan di sini:
- Ulasan yang disembunyikan admin (`is_hidden`) TIDAK muncul di daftar publik,
  tetapi tetap terlihat oleh pemiliknya di `/reviews/me` (supaya penulis tahu
  ulasannya disembunyikan, bukan hilang tanpa kabar).
- Mengubah/menghapus hanya boleh oleh pemilik ulasan atau admin.
- Satu pengguna satu ulasan per film. Diperiksa di sini agar pesannya ramah,
  dan ditegakkan juga oleh unique index di database sebagai lapis terakhir.
"""
from __future__ import annotations

from app.core.constants import Role
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.core.pagination import Pagination
from app.movies import service as movie_service
from app.reviews import repository as repo


def _ensure_movie_exists(movie_id: int) -> dict:
    """Memastikan film yang diulas benar-benar ada sebelum menulis ulasan.

    Tanpa ini, database menolak lewat foreign key dan pengguna menerima 500,
    padahal ini kesalahan masukan (film tidak ada) yang seharusnya 404.
    """
    return movie_service.find_movie_by_id(movie_id)


def list_movie_reviews(movie_id: int, pagination: Pagination | None = None) -> dict:
    _ensure_movie_exists(movie_id)
    items, total = repo.find_by_movie(movie_id, pagination)
    return {"items": items, "total": total}


def list_my_reviews(user_id: str, pagination: Pagination | None = None) -> dict:
    items, total = repo.find_all_by_user(user_id, pagination)
    return {"items": items, "total": total}


def list_for_moderation(pagination: Pagination | None = None) -> dict:
    items, total = repo.find_all_for_moderation(pagination)
    return {"items": items, "total": total}


def create_review(user_id: str, payload: dict) -> dict:
    movie_id = payload["movie_id"]
    _ensure_movie_exists(movie_id)

    existing = repo.find_by_user_and_movie(user_id, movie_id)
    if existing:
        raise ConflictError(
            "Kamu sudah pernah mengulas film ini. Ubah ulasan yang sudah ada "
            f"(id {existing['id']}) atau hapus dulu."
        )

    created = repo.create(
        {
            "user_id": user_id,
            "movie_id": movie_id,
            "rating": payload["rating"],
            "content": payload["content"],
        }
    )
    if not created:
        raise BadRequestError("Ulasan gagal disimpan")
    return get_review(created["id"])


def get_review(review_id: int) -> dict:
    review = repo.find_by_id(review_id)
    if not review:
        raise NotFoundError(f"Ulasan dengan id {review_id} tidak ditemukan")
    return review


def update_review(review_id: int, payload: dict, current_user: dict) -> dict:
    review = get_review(review_id)
    _ensure_can_modify(review, current_user)

    if not payload:
        raise BadRequestError("Tidak ada perubahan yang dikirim")

    updated = repo.update(review_id, payload)
    if not updated:
        raise NotFoundError(f"Ulasan dengan id {review_id} tidak ditemukan")
    return get_review(review_id)


def delete_review(review_id: int, current_user: dict) -> None:
    review = get_review(review_id)
    _ensure_can_modify(review, current_user)
    repo.delete(review_id)


def set_hidden(review_id: int, is_hidden: bool) -> dict:
    """Moderasi admin: sembunyikan/tampilkan ulasan tanpa menghapusnya."""
    get_review(review_id)
    updated = repo.set_hidden(review_id, is_hidden)
    if not updated:
        raise NotFoundError(f"Ulasan dengan id {review_id} tidak ditemukan")
    return get_review(review_id)


def _ensure_can_modify(review: dict, current_user: dict) -> None:
    is_owner = str(review["user_id"]) == str(current_user["user_id"])
    is_admin = current_user.get("role") == Role.admin.value
    if not (is_owner or is_admin):
        raise ForbiddenError("Tidak diizinkan mengubah ulasan milik pengguna lain")
