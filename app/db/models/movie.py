"""Tabel `movies`."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Movie(Base):
    __tablename__ = "movies"
    __table_args__ = (
        # Ditambahkan di migrasi 0003 (NOT VALID agar data lama tidak menggagalkan migrasi).
        CheckConstraint("rating IS NULL OR (rating >= 0 AND rating <= 10)", name="rating_range"),
        CheckConstraint("release_year IS NULL OR (release_year >= 1888 AND release_year <= 2100)", name="release_year_range"),
        Index("idx_movies_title", "title"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    release_year: Mapped[int | None] = mapped_column(Integer)
    genre: Mapped[str | None] = mapped_column(String(255))
    director: Mapped[str | None] = mapped_column(String(255))
    overview: Mapped[str | None] = mapped_column(Text)
    poster_url: Mapped[str | None] = mapped_column(Text)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
    created_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now())
