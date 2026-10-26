"""Hash password dan JWT (tanpa database)."""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.core.security import create_access_token, decode_token, hash_password, pwd_context, verify_password


def test_hash_bukan_plaintext_dan_bisa_diverifikasi():
    hashed = hash_password("rahasia123")
    assert hashed != "rahasia123" and hashed.startswith("$pbkdf2-sha256$600000$")
    assert verify_password("rahasia123", hashed)
    assert not verify_password("salah", hashed)
    assert not verify_password("apa saja", None)


def test_hash_lama_29000_rounds_masih_valid_dan_ditandai_perlu_upgrade():
    legacy = pwd_context.using(pbkdf2_sha256__rounds=29_000).hash("rahasia123")
    assert verify_password("rahasia123", legacy)
    assert pwd_context.needs_update(legacy)


def _hash_sha256_lama(password: str) -> str:
    """Meniru 8 hash SHA-256 lama yang dulu membuat login meledak jadi HTTP 500."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def test_hash_format_asing_ditolak_bukan_meledak():
    # Bentuk apa pun yang bukan milik passlib harus mengembalikan False,
    # bukan melempar pengecualian (penyebab error 500 saat login dulu).
    for aneh in (
        "5f4dcc3b5aa765d61d8327deb882cf99",          # hex sha256 32 karakter (format lama)
        _hash_sha256_lama("rahasia123"),            # sha256 64 karakter
        "hash-palsu",                                # bukan format apa pun
        "$pbkdf2-sha256$abc$xx$yy",                  # pbkdf2 tapi rusak
        "$2b$12$" + "x" * 53,                        # bcrypt yang tidak didukung konteks
    ):
        assert verify_password("rahasia123", aneh) is False, aneh


def test_hash_rusak_tidak_bikin_login_500():
    # Inti perbaikannya: verify_password tidak boleh menaikkan UnknownHashError.
    try:
        assert verify_password("salah", "abcdef1234567890") is False
    except Exception as exc:  # pragma: no cover - hanya jalan kalau bug kembali
        raise AssertionError(f"verify_password meledak lagi: {type(exc).__name__}: {exc}") from exc


def test_token_berisi_claim_wajib():
    payload = decode_token(create_access_token("abc", "admin"))
    assert payload["sub"] == "abc" and payload["role"] == "admin" and "exp" in payload and "iat" in payload


def _forge(**overrides) -> str:
    settings = get_settings()
    payload = {"sub": "abc", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)} | overrides.pop("payload", {})
    return jwt.encode(payload, overrides.get("key", settings.SECRET_KEY), algorithm=overrides.get("alg", "HS256"))


def test_token_kedaluwarsa_ditolak():
    expired = _forge(payload={"exp": datetime.now(timezone.utc) - timedelta(minutes=1)})
    with pytest.raises(UnauthorizedError, match="kedaluwarsa"):
        decode_token(expired)


def test_token_secret_salah_atau_rusak_ditolak():
    with pytest.raises(UnauthorizedError):
        decode_token(_forge(key="k" * 40 + "x"))
    with pytest.raises(UnauthorizedError):
        decode_token("bukan.token.jwt")


def test_token_alg_none_ditolak():
    unsigned = jwt.encode({"sub": "abc"}, key=None, algorithm="none")
    with pytest.raises(UnauthorizedError):
        decode_token(unsigned)


def test_token_tanpa_exp_ditolak_walau_tanda_tangan_benar():
    # Token tanpa masa berlaku tidak boleh diterima, meski ditandatangani dengan secret yang benar.
    settings = get_settings()
    token = jwt.encode({"sub": "abc"}, settings.SECRET_KEY, algorithm="HS256")
    with pytest.raises(UnauthorizedError):
        decode_token(token)


def test_token_tanpa_sub_ditolak():
    settings = get_settings()
    token = jwt.encode({"exp": datetime.now(timezone.utc) + timedelta(minutes=5)}, settings.SECRET_KEY, algorithm="HS256")
    with pytest.raises(UnauthorizedError):
        decode_token(token)
