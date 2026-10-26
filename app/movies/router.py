"""Peta endpoint modul movies.

Dulu: @app.get("/movies") menempel di main.py.
Sekarang: berkas kecil berisi daftar alamat + pagar akses saja.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import require_admin
from app.core.pagination import Pagination, pagination_params
from app.movies import service
from app.movies.schemas import MovieCreate, MovieUpdate

router = APIRouter(prefix="/movies", tags=["Movies Catalog"])


def _envelope(data, message: str, **extra) -> dict:
    return {"success": True, "message": message, "data": data, **extra}


@router.get("")
def list_movies(
    search: str | None = Query(None, description="Cari film berdasarkan judul"),
    genre: str | None = Query(None, description="Filter berdasarkan genre"),
    pagination: Pagination = Depends(pagination_params),
):
    result = service.get_movies(search=search, genre=genre, pagination=pagination)
    return {
        "success": True,
        "count": len(result["items"]),
        "total": result["total"],
        "page": pagination.page,
        "limit": pagination.limit,
        "data": result["items"],
    }


@router.get("/{movie_id}")
def get_movie_detail(movie_id: int):
    movie = service.find_movie_by_id(movie_id)
    return _envelope(movie, "Detail film berhasil diambil")


@router.post("", status_code=201)
def create_movie(payload: MovieCreate, admin: dict = Depends(require_admin)):
    movie = service.create_movie(payload, admin_id=admin["user_id"])
    return _envelope(movie, "Film berhasil ditambahkan")


@router.put("/{movie_id}")
def update_movie(movie_id: int, payload: MovieUpdate, admin: dict = Depends(require_admin)):
    movie = service.update_movie(movie_id, payload, admin_id=admin["user_id"])
    return _envelope(movie, "Film berhasil diupdate")


@router.delete("/{movie_id}")
def delete_movie(movie_id: int, admin: dict = Depends(require_admin)):
    movie = service.delete_movie(movie_id, admin_id=admin["user_id"])
    return _envelope(movie, "Film berhasil dihapus")
