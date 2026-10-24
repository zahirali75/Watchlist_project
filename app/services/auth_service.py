"""Aturan bisnis autentikasi (register & login)."""
from __future__ import annotations

from app.core.constants import AuditType, Role
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.repositories import user_repository as repo
from app.schemas.audit_log_schema import AuditLogCreate
from app.schemas.auth_schema import RegisterUser
from app.services import audit_log_service

# Pesan sengaja dibuat sama untuk email tidak ada & password salah, supaya
# penyerang tidak bisa memakai endpoint login untuk menebak email terdaftar.
INVALID_CREDENTIALS = "Email atau password salah"


def register_user(data: RegisterUser) -> dict:
    if repo.find_by_email(data.email):
        raise ConflictError("Email sudah terdaftar", meta={"email": data.email})

    payload = {
        "email": data.email,
        "password_hash": hash_password(data.password),
        "name": data.name or "",
        "role": Role.user.value,
    }
    user = repo.create(payload)
    if not user:
        raise UnauthorizedError("Gagal menyimpan user ke database")

    audit_log_service.create_audit_log(
        AuditLogCreate(
            context=f"User baru terdaftar: {user.get('email')} (ID: {user.get('id')})",
            type=AuditType.USER_REGISTER.value,
        ),
        actor_id=str(user.get("id")),
    )

    return {
        "userId": str(user.get("id")),
        "email": user.get("email"),
        "name": user.get("name"),
        "role": user.get("role", Role.user.value),
        "accessToken": create_access_token(user.get("id"), user.get("role", Role.user.value)),
    }


def authenticate_user(email: str, password: str) -> dict:
    user = repo.find_auth_by_email(email)
    if not user or not verify_password(password, user.get("password_hash")):
        raise UnauthorizedError(INVALID_CREDENTIALS)

    return {
        "userId": str(user.get("id")),
        "email": user.get("email"),
        "name": user.get("name"),
        "role": user.get("role", Role.user.value),
        "accessToken": create_access_token(user.get("id"), user.get("role", Role.user.value)),
    }
