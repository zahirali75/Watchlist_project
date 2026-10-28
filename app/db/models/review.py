"""Tabel `reviews` (ulasan film oleh pengguna)."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating >= 0 AND rating <= 10", name="rating_range"),
        # Satu pengguna hanya boleh punya satu ulasan per film. Ditegakkan di
        # database, bukan hanya diperiksa di kode, supaya dua request bersamaan
        # tidak bisa menghasilkan ulasan kembar.
        Index("uq_reviews_user_id_movie_id", "user_id", "movie_id", unique=True),
        Index("idx_reviews_movie_id", "movie_id"),
        Index("idx_reviews_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    movie_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Moderasi: ulasan tersembunyi tetap ada dan tetap terlihat oleh pemiliknya,
    # hanya tidak ditampilkan pada daftar publik.
    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
