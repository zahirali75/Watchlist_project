"""Aturan bisnis autentikasi (register & login)."""
from __future__ import annotations

import logging
from functools import lru_cache

from app.core.constants import AuditType, Role
from app.core.config import get_settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.rate_limit import login_throttle
from app.core.security import create_access_token, hash_password, pwd_context, verify_password
from app.audit_logs import service as audit_log_service
from app.audit_logs.schemas import AuditLogCreate
from app.auth.schemas import RegisterUser
from app.users import service as user_service

logger = logging.getLogger("app.auth")

# Pesan sengaja dibuat sama untuk email tidak ada & password salah, supaya
# penyerang tidak bisa memakai endpoint login untuk menebak email terdaftar.
INVALID_CREDENTIALS = "Email atau password salah"


def register_user(data: RegisterUser) -> dict:
    if user_service.find_by_email(data.email):
        raise ConflictError("Email sudah terdaftar", meta={"email": data.email})

    payload = {
        "email": data.email,
        "password_hash": hash_password(data.password),
        "name": data.name or "",
        "role": Role.user.value,
    }
    user = user_service.create_user(payload)
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


@lru_cache
def _dummy_hash() -> str:
    """Hash palsu agar login email tak dikenal tetap memakan waktu verifikasi yang sama."""
    return hash_password("dummy-password-for-timing")


def authenticate_user(email: str, password: str, client_ip: str | None = None) -> dict:
    settings = get_settings()
    throttle_key = login_throttle.key(client_ip, email)
    ip_key = login_throttle.ip_key(client_ip)
    login_throttle.check(throttle_key, settings.LOGIN_MAX_ATTEMPTS, settings.LOGIN_WINDOW_SECONDS)
    login_throttle.check(ip_key, settings.LOGIN_IP_MAX_ATTEMPTS, settings.LOGIN_WINDOW_SECONDS)

    user = user_service.find_auth_by_email(email)
    stored_hash = user.get("password_hash") if user else None
    if not stored_hash:
        verify_password(password, _dummy_hash())  # samakan waktu respons (cegah user enumeration)
    if not user or not verify_password(password, stored_hash):
        login_throttle.record_failure(throttle_key)
        login_throttle.record_failure(ip_key)
        logger.warning("Login gagal (ip=%s)", client_ip)  # email/password tidak dicatat
        raise UnauthorizedError(INVALID_CREDENTIALS)
    login_throttle.reset(throttle_key)

    # Upgrade older, valid PBKDF2 hashes after successful authentication.
    if stored_hash and pwd_context.needs_update(stored_hash):
        try:
            user_service.update_password_hash(str(user.get("id")), hash_password(password))
        except Exception:
            # Do not lock a valid user out solely because hash migration failed.
            logger.exception("Gagal memperbarui parameter hash password untuk user %s", user.get("id"))

    return {
        "userId": str(user.get("id")),
        "email": user.get("email"),
        "name": user.get("name"),
        "role": user.get("role", Role.user.value),
        "accessToken": create_access_token(user.get("id"), user.get("role", Role.user.value)),
    }
