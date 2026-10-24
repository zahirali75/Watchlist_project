"""Penerjemah error database + eksekutor query.

Setara dengan common/exceptions/sql.error.ts di repo Pola: error mentah dari
driver database diubah jadi error domain yang enak dibaca.
"""
from __future__ import annotations

import logging

from postgrest.exceptions import APIError

from app.core.exceptions import BadRequestError, ConflictError, UpstreamError

logger = logging.getLogger("cinelist")


def run(query):
    """Jalankan query PostgREST, terjemahkan error yang muncul."""
    try:
        return query.execute()
    except APIError as exc:
        code = str(getattr(exc, "code", "") or "")
        message = str(getattr(exc, "message", "") or exc)
        if code == "23505" or "duplicate key" in message.lower():
            raise ConflictError(
                "Data sudah ada (melanggar unique constraint)",
                meta={"dbCode": code},
            ) from exc
        if code == "23503":
            raise BadRequestError(
                "Referensi tidak valid (foreign key tidak ditemukan)",
                meta={"dbCode": code},
            ) from exc
        if code == "42501":
            raise UpstreamError(
                "Akses ditolak database (cek kunci Supabase / RLS)",
                meta={"dbCode": code},
            ) from exc
        raise UpstreamError("Database menolak permintaan", meta={"dbCode": code, "dbMessage": message}) from exc
    except Exception as exc:  # jaringan, timeout, dll
        logger.exception("Query Supabase gagal")
        raise UpstreamError("Gagal berkomunikasi dengan database") from exc


def first_or_none(response):
    return response.data[0] if response.data else None
