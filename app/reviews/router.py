"""Endpoint ulasan (/reviews).

Semua jalur butuh token:
- `GET /reviews/movie/{movie_id}` sengaja tetap butuh login supaya konsisten
  dengan sisa modul yang menyimpan data per-pengguna (film & watchlist), dan
  supaya tidak ada satu pun jalur publik yang membocorkan daftar penulis ulasan.
  Halaman detail film di frontend hanya dapat dibuka setelah login.
- `POST`/`PUT`/`DELETE` memakai pemilik ulasan atau admin (diperiksa di service).
- `GET /reviews/moderation` + `PATCH /reviews/{id}/moderation` khusus admin.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import get_current_user, require_admin
from app.core.pagination import Pagination, pagination_params
from app.reviews import service
from app.reviews.schemas import ReviewCreate, ReviewModeration, ReviewUpdate

router = APIRouter(prefix="/reviews", tags=["Reviews"])

# Didaftarkan SEBELUM rute ber-{review_id} supaya "me"/"moderation" tidak
# tertangkap sebagai id (rute statis vs parametrik).
moderation_router = APIRouter(prefix="/reviews/moderation", tags=["Reviews"], dependencies=[Depends(require_admin)])


def _paginated(result: dict, pagination: Pagination) -> dict:
    """Envelope daftar berhalaman - bentuknya SAMA dengan /movies dan /watchlists.

    `count/total/page/limit` sejajar dengan `data` di root (bukan di dalam objek
    `meta`), supaya frontend bisa memakai satu bentuk parsing untuk semua daftar.
    """
    return {
        "success": True,
        "count": len(result["items"]),
        "total": result["total"],
        "page": pagination.page,
        "limit": pagination.limit,
        "data": result["items"],
    }


@router.get("/me")
def list_my_reviews(
    pagination: Pagination = Depends(pagination_params),
    current_user: dict = Depends(get_current_user),
):
    """Ulasan milik sendiri (termasuk yang disembunyikan admin)."""
    return _paginated(service.list_my_reviews(current_user["user_id"], pagination), pagination)


@router.get("/movie/{movie_id}")
def list_movie_reviews(
    movie_id: int,
    pagination: Pagination = Depends(pagination_params),
    current_user: dict = Depends(get_current_user),
):
    """Ulasan publik sebuah film."""
    return _paginated(service.list_movie_reviews(movie_id, pagination), pagination)


@moderation_router.get("")
def list_reviews_for_moderation(
    pagination: Pagination = Depends(pagination_params),
):
    """Daftar seluruh ulasan untuk ditinjau admin (termasuk yang disembunyikan)."""
    return _paginated(service.list_for_moderation(pagination), pagination)


@router.get("/{review_id}")
def get_review(review_id: int, current_user: dict = Depends(get_current_user)):
    review = service.get_review(review_id)
    return {"success": True, "data": review}


@router.post("", status_code=201)
def create_review(payload: ReviewCreate, current_user: dict = Depends(get_current_user)):
    review = service.create_review(current_user["user_id"], payload.model_dump())
    return {"success": True, "message": "Ulasan berhasil dibuat", "data": review}


@router.put("/{review_id}")
def update_review(
    review_id: int,
    payload: ReviewUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Penggantian parsial: kirim hanya field yang berubah."""
    review = service.update_review(review_id, payload.model_dump(exclude_unset=True), current_user)
    return {"success": True, "message": "Ulasan berhasil diupdate", "data": review}


@router.patch("/{review_id}/moderation")
def moderate_review(
    review_id: int,
    payload: ReviewModeration,
    admin: dict = Depends(require_admin),  # noqa: ARG001 - kehadirannya yang menjaga akses
):
    review = service.set_hidden(review_id, payload.is_hidden)
    state = "disembunyikan" if payload.is_hidden else "ditampilkan kembali"
    return {"success": True, "message": f"Ulasan berhasil {state}", "data": review}


@router.delete("/{review_id}")
def delete_review(review_id: int, current_user: dict = Depends(get_current_user)):
    service.delete_review(review_id, current_user)
    return {"success": True, "message": "Ulasan berhasil dihapus"}
