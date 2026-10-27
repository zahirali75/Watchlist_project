"""Query PostgreSQL untuk refresh token & token reset password.

Hanya hash token yang disimpan (lihat app/core/security.py), jadi isi tabel ini
tidak bisa dipakai langsung untuk login walau bocor.
"""
from __future__ import annotations

from typing import Any

from app.db.executor import execute_returning, execute_returning_all, fetch_one

# --- Refresh token (perpanjangan sesi) -------------------------------------


def create_refresh_token(payload: dict[str, Any]) -> dict | None:
    return execute_returning(
        """INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
           VALUES (:user_id, :token_hash, :expires_at)
           RETURNING id, user_id, expires_at, revoked_at, created_at""",
        payload,
    )


def find_refresh_token(token_hash: str) -> dict | None:
    return fetch_one(
        "SELECT id, user_id, expires_at, revoked_at FROM refresh_tokens WHERE token_hash = :token_hash",
        {"token_hash": token_hash},
    )


def revoke_refresh_token(token_id: str) -> bool:
    row = execute_returning(
        "UPDATE refresh_tokens SET revoked_at = CURRENT_TIMESTAMP WHERE id = :token_id RETURNING id",
        {"token_id": token_id},
    )
    return row is not None


def revoke_all_refresh_tokens(user_id: str) -> int:
    """Cabut SEMUA sesi milik satu user (dipakai saat ganti/lupa password)."""
    rows = execute_returning_all(
        "UPDATE refresh_tokens SET revoked_at = CURRENT_TIMESTAMP "
        "WHERE user_id = :user_id AND revoked_at IS NULL RETURNING id",
        {"user_id": user_id},
    )
    return len(rows)


def delete_expired_refresh_tokens() -> int:
    """Bersih-bersih: hapus token yang sudah lewat masa berlakunya."""
    rows = execute_returning_all(
        "DELETE FROM refresh_tokens WHERE expires_at < CURRENT_TIMESTAMP RETURNING id",
    )
    return len(rows)


# --- Token reset password ---------------------------------------------------


def create_password_reset(payload: dict[str, Any]) -> dict | None:
    return execute_returning(
        """INSERT INTO password_resets (user_id, token_hash, expires_at)
           VALUES (:user_id, :token_hash, :expires_at)
           RETURNING id, user_id, expires_at, used_at""",
        payload,
    )


def find_password_reset(token_hash: str) -> dict | None:
    return fetch_one(
        "SELECT id, user_id, expires_at, used_at FROM password_resets WHERE token_hash = :token_hash",
        {"token_hash": token_hash},
    )


def mark_password_reset_used(reset_id: str) -> bool:
    row = execute_returning(
        "UPDATE password_resets SET used_at = CURRENT_TIMESTAMP WHERE id = :reset_id RETURNING id",
        {"reset_id": reset_id},
    )
    return row is not None
