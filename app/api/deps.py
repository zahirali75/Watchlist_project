"""Dependency bersama: pembaca JWT + penjaga role.

Setara middleware/auth.ts (authenticateJWT + authorizeAdmin) di repo Pola.
"""
from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.constants import Role
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token

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

    return {"user_id": str(subject), "role": payload.get("role", Role.user.value)}


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != Role.admin.value:
        raise ForbiddenError("Akses ditolak: hanya admin yang diizinkan")
    return current_user
