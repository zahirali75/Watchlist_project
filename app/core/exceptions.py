"""Kelas error domain.

Dulu tiap endpoint menulis try/except + raise HTTPException(500, str(e)).
Karena str(e) mentah, detail database ikut bocor ke klien. Sekarang service
hanya melempar kelas ini; penerjemahannya ke HTTP ada di satu tempat
(core/error_handlers.py).
"""
from __future__ import annotations

from typing import Any


class AppError(Exception):
    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
        meta: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.meta = meta
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code


class BadRequestError(AppError):
    status_code = 400
    code = "BAD_REQUEST"


class UnauthorizedError(AppError):
    status_code = 401
    code = "UNAUTHORIZED"


class ForbiddenError(AppError):
    status_code = 403
    code = "FORBIDDEN"


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"


class TooManyRequestsError(AppError):
    status_code = 429
    code = "TOO_MANY_REQUESTS"


class UpstreamError(AppError):
    """Database or network connectivity problem."""
    status_code = 502
    code = "UPSTREAM_ERROR"
