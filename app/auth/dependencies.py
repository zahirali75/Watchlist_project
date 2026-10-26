"""Dependency autentikasi & otorisasi (dipakai semua fitur).

- get_current_user : membaca JWT, lalu memastikan user MASIH ADA di database
                     dan memakai ROLE TERKINI dari database (bukan dari token).
                     Jadi admin yang dicabut haknya / user yang dihapus langsung
                     kehilangan akses walau tokennya belum kedaluwarsa.
- require_admin    : penjaga endpoint khusus admin (403 untuk user biasa).
"""
from __future__ import annotations

import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.constants import Role
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.logging import get_logger
from app.core.security import decode_token
from app.users import service as user_service

logger = get_logger("auth")

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if credentials is None:
        raise UnauthorizedError("Token tidak disertakan")

    payload = decode_token(credentials.credentials)
    subject = payload.get("sub")
    if not subject:
        raise UnauthorizedError("Token tidak memiliki sub")
    try:
        user_id = str(uuid.UUID(str(subject)))
    except ValueError as exc:
        raise UnauthorizedError("Token tidak valid") from exc

    identity = user_service.find_identity(user_id)
    if not identity:
        logger.warning("Token ditolak: user %s tidak ditemukan", user_id)
        raise UnauthorizedError("User tidak ditemukan")

    return {"user_id": user_id, "role": identity.get("role") or Role.user.value}


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != Role.admin.value:
        raise ForbiddenError("Akses ditolak: hanya admin yang diizinkan")
    return current_user
