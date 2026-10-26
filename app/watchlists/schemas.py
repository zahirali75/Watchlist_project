"""Kontrak input/output untuk modul watchlists."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class WatchStatus(str, Enum):
    want_to_watch = "want_to_watch"
    watching = "watching"
    watched = "watched"


class WatchlistCreate(BaseModel):
    movie_id: int
    status: WatchStatus = WatchStatus.want_to_watch
    notes: str | None = Field(None, max_length=2000)


class WatchlistUpdate(BaseModel):
    """Semua opsional -> hanya field yang dikirim yang diubah (exclude_unset)."""
    status: WatchStatus | None = None
    notes: str | None = Field(None, max_length=2000)


class WatchlistRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    movie_id: int
    status: WatchStatus
    notes: str | None = None
