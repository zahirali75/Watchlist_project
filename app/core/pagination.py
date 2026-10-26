"""Parameter paginasi sebagai dependency yang bisa dipakai ulang."""
from __future__ import annotations

from pydantic import BaseModel
from fastapi import Query

from app.core.config import get_settings
from app.core.exceptions import BadRequestError


class Pagination(BaseModel):
    page: int
    limit: int
    offset: int

    @property
    def start(self) -> int:
        return self.offset

    @property
    def end(self) -> int:
        return self.offset + self.limit - 1


def pagination_params(
    page: int = Query(1, ge=1, le=1_000_000, description="Halaman (mulai dari 1, maksimal 1.000.000)"),
    limit: int = Query(0, ge=0, le=1000, description="Jumlah item per halaman"),
) -> Pagination:
    settings = get_settings()
    if limit == 0:
        limit = settings.DEFAULT_PAGE_SIZE
    if limit > settings.MAX_PAGE_SIZE:
        raise BadRequestError(
            f"limit maksimal {settings.MAX_PAGE_SIZE}",
            meta={"maxLimit": settings.MAX_PAGE_SIZE},
        )
    offset = (page - 1) * limit
    return Pagination(page=page, limit=limit, offset=offset)
