"""Kontrak input untuk modul users."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    """Yang boleh diubah pengguna untuk dirinya sendiri: hanya nama tampilan."""

    name: str = Field(..., min_length=1, max_length=255)
