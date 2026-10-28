"""Kontrak input untuk modul reviews.

Bentuk respons tidak diikat `response_model` supaya konsisten dengan modul lain
(modul watchlists/movies juga mengembalikan dict dari service). Yang dijaga di
sini adalah aturan INPUT: rating 0-10 dan panjang isi ulasan.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    movie_id: int
    rating: float = Field(..., ge=0, le=10)
    content: str = Field(..., min_length=1, max_length=5000)


class ReviewUpdate(BaseModel):
    """Parsial: hanya field yang dikirim yang diubah (exclude_unset).

    Rating dan isi ulasan boleh dikosongkan satu-satu, tetapi tidak boleh
    keduanya sekaligus - aturan itu diperiksa di service supaya pesannya jelas.
    """

    rating: float | None = Field(None, ge=0, le=10)
    content: str | None = Field(None, min_length=1, max_length=5000)


class ReviewModeration(BaseModel):
    """Admin menyembunyikan atau menampilkan kembali ulasan."""

    is_hidden: bool
