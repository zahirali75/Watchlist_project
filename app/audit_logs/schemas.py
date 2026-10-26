"""Kontrak internal untuk pencatatan audit."""
from __future__ import annotations

from pydantic import BaseModel, Field


class AuditLogCreate(BaseModel):
    context: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)
    created_by: str | None = None
