"""Kontrak input/output untuk modul movies.

Dulu semua model menempel di main.py. Sekarang aturan validasi hidup di file
sendiri, jadi aturan bisnis dan aturan input tidak saling mengganggu.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MovieBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    release_year: int = Field(..., ge=1888, le=2100, description="Film pertama dibuat 1888")
    genre: str = Field(..., min_length=1, max_length=255)
    director: str = Field("", max_length=255)
    overview: str = ""
    poster_url: str = ""
    rating: float = Field(0.0, ge=0, le=10)


class MovieCreate(MovieBase):
    pass


class MovieUpdate(MovieBase):
    """Untuk sekarang update bersifat penuh (replace), sama seperti sebelumnya."""


class MovieRead(MovieBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
