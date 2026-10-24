"""Kontrak input/output untuk modul watchlists."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.schemas.common import WatchStatus


class WatchlistCreate(BaseModel):
    movie_id: int
    status: WatchStatus = WatchStatus.want_to_watch
    notes: str | None = None


class WatchlistUpdate(BaseModel):
    """Semua opsional -> hanya field yang dikirim yang diubah (exclude_unset)."""
    status: WatchStatus | None = None
    notes: str | None = None


class WatchlistRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    movie_id: int
    status: WatchStatus
    notes: str | None = None
