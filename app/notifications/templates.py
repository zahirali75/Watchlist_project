"""Isi email yang dikirim aplikasi (dipisah agar mudah ditinjau & diubah)."""
from __future__ import annotations

from app.core.config import get_settings


def password_reset_email(reset_token: str) -> tuple[str, str]:
    """Kembalikan (subjek, isi teks) untuk email lupa password."""
    settings = get_settings()
    link = f"{settings.APP_BASE_URL.rstrip('/')}/reset-password?token={reset_token}"
    subject = f"Atur ulang password {settings.APP_NAME}"
    body = (
        f"Halo,\n\n"
        f"Kami menerima permintaan atur ulang password untuk akun {settings.APP_NAME} ini.\n"
        f"Buka tautan berikut untuk membuat password baru:\n\n"
        f"{link}\n\n"
        f"Tautan berlaku {settings.PASSWORD_RESET_EXPIRE_MINUTES} menit dan hanya bisa dipakai sekali.\n"
        f"Jika kamu tidak meminta ini, abaikan saja email ini - password kamu tidak berubah.\n\n"
        f"Salam,\n{settings.APP_NAME}\n"
    )
    return subject, body
