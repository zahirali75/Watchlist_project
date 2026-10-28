"""Tabel `movies`."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Movie(Base):
    __tablename__ = "movies"
    __table_args__ = (
        # Ditambahkan di migrasi 0003 (NOT VALID agar data lama tidak menggagalkan migrasi).
        CheckConstraint("rating IS NULL OR (rating >= 0 AND rating <= 10)", name="rating_range"),
        CheckConstraint("release_year IS NULL OR (release_year >= 1888 AND release_year <= 2100)", name="release_year_range"),
        # Ditambahkan di migrasi 0007. Nilai 'series', bukan 'tv': backend memakai
        # istilah yang sama dengan tab di aplikasi, dan konversi ke label tampilan
        # adalah urusan frontend.
        CheckConstraint("media_type IN ('movie', 'series')", name="media_type_check"),
        Index("idx_movies_title", "title"),
        Index("idx_movies_media_type", "media_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    release_year: Mapped[int | None] = mapped_column(Integer)
    genre: Mapped[str | None] = mapped_column(String(255))
    director: Mapped[str | None] = mapped_column(String(255))
    overview: Mapped[str | None] = mapped_column(Text)
    poster_url: Mapped[str | None] = mapped_column(Text)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
    media_type: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'movie'"))
    created_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now())
