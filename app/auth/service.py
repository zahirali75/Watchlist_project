"""Aturan bisnis autentikasi: register, login, sesi, dan password.

Catatan desain sesi
-------------------
Access token (JWT) tetap berumur pendek (60 menit) supaya bila bocor, masa
pakainya singkat. Yang membuat pengguna tidak perlu login terus-menerus adalah
REFRESH TOKEN: string acak berumur panjang yang disimpan hash-nya di database
sehingga bisa dicabut (logout, ganti password).

Setiap perpanjangan sesi memakai token baru dan token lama langsung dicabut
(rotasi), jadi token yang pernah bocor tidak bisa dipakai dua kali.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from functools import lru_cache

from app.audit_logs import service as audit_log_service
from app.audit_logs.schemas import AuditLogCreate
from app.auth import repository as token_repo
from app.auth.schemas import RegisterUser
from app.core.config import get_settings
from app.core.constants import AuditType, Role
from app.core.exceptions import BadRequestError, ConflictError, UnauthorizedError
from app.core.rate_limit import login_throttle
from app.core.security import (
    create_access_token,
    generate_opaque_token,
    hash_password,
    hash_token,
    pwd_context,
    verify_password,
)
from app.notifications import service as notification_service
from app.users import service as user_service

logger = logging.getLogger("app.auth")

# Pesan sengaja dibuat sama untuk email tidak ada & password salah, supaya
# penyerang tidak bisa memakai endpoint login untuk menebak email terdaftar.
INVALID_CREDENTIALS = "Email atau password salah"
INVALID_REFRESH_TOKEN = "Sesi tidak valid atau sudah berakhir"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _expired(value: datetime | None) -> bool:
    """True bila waktunya sudah lewat. Menangani nilai naive dari database."""
    if value is None:
        return False
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value <= _now()


def _issue_refresh_token(user_id: str) -> str:
    settings = get_settings()
    raw_token = generate_opaque_token()
    token_repo.create_refresh_token(
        {
            "user_id": str(user_id),
            "token_hash": hash_token(raw_token),
            "expires_at": _now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        }
    )
    return raw_token


def _session_payload(user: dict, refresh_token: str | None = None) -> dict:
    return {
        "userId": str(user.get("id")),
        "email": user.get("email"),
        "name": user.get("name"),
        "role": user.get("role", Role.user.value),
        "accessToken": create_access_token(user.get("id"), user.get("role", Role.user.value)),
        "refreshToken": refresh_token,
    }


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

    return _session_payload(user, _issue_refresh_token(user.get("id")))


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

    return _session_payload(user, _issue_refresh_token(user.get("id")))


# ---------------------------------------------------------------------------
# Sesi: perpanjangan & logout
# ---------------------------------------------------------------------------
def refresh_session(refresh_token: str) -> dict:
    """Tukar refresh token lama dengan access token + refresh token baru."""
    stored = token_repo.find_refresh_token(hash_token(refresh_token))
    if not stored or stored.get("revoked_at") is not None or _expired(stored.get("expires_at")):
        raise UnauthorizedError(INVALID_REFRESH_TOKEN)

    identity = user_service.find_identity(str(stored["user_id"]))
    if not identity:
        # User sudah dihapus -> sesinya tidak ada gunanya lagi.
        raise UnauthorizedError(INVALID_REFRESH_TOKEN)

    # Rotasi: token lama langsung dicabut supaya tidak bisa dipakai ulang.
    token_repo.revoke_refresh_token(str(stored["id"]))

    user_id = str(stored["user_id"])
    return {
        "userId": user_id,
        "role": identity.get("role") or Role.user.value,
        "accessToken": create_access_token(user_id, identity.get("role") or Role.user.value),
        "refreshToken": _issue_refresh_token(user_id),
    }


def logout(refresh_token: str, current_user_id: str) -> dict:
    """Cabut SATU sesi (perangkat ini saja). Idempoten: token asing tetap 'berhasil'."""
    stored = token_repo.find_refresh_token(hash_token(refresh_token))
    if stored and str(stored["user_id"]) == str(current_user_id) and stored.get("revoked_at") is None:
        token_repo.revoke_refresh_token(str(stored["id"]))
    return {"revoked": True}


# ---------------------------------------------------------------------------
# Password: ganti (sudah login) & lupa (lewat email)
# ---------------------------------------------------------------------------
def change_password(user_id: str, current_password: str, new_password: str) -> dict:
    user = user_service.find_auth_by_email_by_id(user_id)
    if not user:
        raise UnauthorizedError("User tidak ditemukan")
    if not verify_password(current_password, user.get("password_hash")):
        raise UnauthorizedError("Password saat ini salah")
    if verify_password(new_password, user.get("password_hash")):
        raise BadRequestError("Password baru tidak boleh sama dengan password lama")

    user_service.update_password_hash(user_id, hash_password(new_password))
    # Seluruh sesi lain dicabut: kalau password berubah karena akun disalahgunakan,
    # penyerang langsung kehilangan akses.
    revoked = token_repo.revoke_all_refresh_tokens(user_id)

    audit_log_service.create_audit_log(
        AuditLogCreate(context=f"Password diganti oleh user ID: {user_id}", type=AuditType.USER_CHANGE_PASSWORD.value),
        actor_id=user_id,
    )
    return {"sessionsRevoked": revoked}


def request_password_reset(email: str) -> dict:
    """Selalu menjawab sama, baik email terdaftar atau tidak (anti penebakan akun)."""
    user = user_service.find_auth_by_email(email)
    message = "Bila email terdaftar, tautan atur ulang password sudah dikirim"

    if not user:
        logger.info("Permintaan reset untuk email yang tidak terdaftar (tidak ada email dikirim)")
        return {"message": message, "emailSent": False}

    settings = get_settings()
    raw_token = generate_opaque_token()
    token_repo.create_password_reset(
        {
            "user_id": str(user["id"]),
            "token_hash": hash_token(raw_token),
            "expires_at": _now() + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES),
        }
    )
    email_sent = notification_service.send_password_reset_email(str(user["email"]), raw_token)
    return {"message": message, "emailSent": email_sent}


def reset_password(token: str, new_password: str) -> dict:
    stored = token_repo.find_password_reset(hash_token(token))
    if not stored or stored.get("used_at") is not None or _expired(stored.get("expires_at")):
        raise BadRequestError("Tautan atur ulang password tidak valid atau sudah kedaluwarsa")

    user_id = str(stored["user_id"])
    user_service.update_password_hash(user_id, hash_password(new_password))
    token_repo.mark_password_reset_used(str(stored["id"]))
    revoked = token_repo.revoke_all_refresh_tokens(user_id)

    audit_log_service.create_audit_log(
        AuditLogCreate(context=f"Password diatur ulang via tautan email (user ID: {user_id})", type=AuditType.USER_PASSWORD_RESET.value),
        actor_id=user_id,
    )
    return {"sessionsRevoked": revoked}
