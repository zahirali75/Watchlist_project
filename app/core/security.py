"""Hashing password + pembuatan/pembacaan JWT."""
from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError

logger = logging.getLogger("app.security")

# OWASP recommends >=600,000 PBKDF2-HMAC-SHA256 iterations when PBKDF2 is used.
# Existing hashes retain their encoded rounds and remain verifiable.
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
    pbkdf2_sha256__rounds=600_000,
)


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        return pwd_context.verify(plain_password, password_hash)
    except ValueError:
        # passlib melempar UnknownHashError (turunan ValueError) untuk hash yang
        # formatnya tidak dikenali — mis. sisa hash SHA-256 lama. Dulu pengecualian
        # ini lolos ke lapisan API dan berubah jadi HTTP 500 saat login.
        # Hash yang tidak dikenali = kredensial tidak sah, jadi ditolak sebagai False.
        logger.warning("password_hash dengan format tidak dikenali ditolak (panjang=%d)", len(password_hash))
        return False


def create_access_token(subject: str | int, role: str = "user") -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(subject),
        "role": role,
        "iat": datetime.now(timezone.utc),
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    settings = get_settings()
    try:
        # Algoritma diset eksplisit (bukan dari input token) dan klaim exp/sub wajib ada.
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Token kedaluwarsa") from exc
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Token tidak valid") from exc


# ---------------------------------------------------------------------------
# Token buram (refresh token & token reset password)
#
# Keduanya adalah string acak, bukan JWT. Alasannya: token seperti ini harus
# bisa DICABUT sebelum masa berlakunya habis (logout, ganti password). JWT tidak
# bisa dicabut tanpa menyimpan daftar hitam, jadi kita simpan hash-nya di tabel.
#
# Yang masuk database hanya hash SHA-256, bukan token aslinya.
# ---------------------------------------------------------------------------
def generate_opaque_token(nbytes: int = 48) -> str:
    """Token acak yang aman dipakai di URL atau body JSON."""
    return secrets.token_urlsafe(nbytes)


def hash_token(raw_token: str) -> str:
    """SHA-256 heksadesimal (64 karakter) untuk disimpan di database."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
