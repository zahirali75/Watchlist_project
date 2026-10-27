"""Pengiriman email.

Bila SMTP belum diatur di .env, email TIDAK dikirim: isinya hanya ditulis ke log
server agar alur lupa password tetap bisa dicoba saat pengembangan. Di mode
produksi, log seperti itu dimatikan supaya tautan reset (yang setara password)
tidak pernah masuk berkas log.
"""
from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.core.config import get_settings
from app.core.logging import get_logger
from app.notifications.templates import password_reset_email

logger = get_logger("notifications")


def _smtp_configured() -> bool:
    return bool(get_settings().SMTP_HOST)


def _send(to_email: str, subject: str, body: str) -> bool:
    settings = get_settings()
    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
        return True
    except Exception:
        # Email gagal TIDAK boleh menggagalkan permintaan pengguna; mereka
        # tetap mendapat jawaban yang sama (mencegah penebakan email terdaftar).
        logger.exception("Gagal mengirim email ke penerima (alamat tidak dicatat)")
        return False


def send_password_reset_email(to_email: str, reset_token: str) -> bool:
    """Kirim tautan reset. Mengembalikan True bila email benar-benar terkirim."""
    subject, body = password_reset_email(reset_token)

    if not _smtp_configured():
        settings = get_settings()
        if settings.is_production:
            logger.warning("SMTP belum diatur; email reset TIDAK dikirim ke %s", to_email)
        else:
            # Mode pengembangan: tautan dimunculkan di log agar bisa dicoba manual.
            logger.warning("SMTP belum diatur. Email reset untuk %s:\n%s", to_email, body)
        return False

    return _send(to_email, subject, body)
