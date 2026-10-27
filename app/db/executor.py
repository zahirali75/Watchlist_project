"""Shared SQLAlchemy Core query helpers and safe database error translation."""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.exceptions import BadRequestError, ConflictError, UpstreamError
from app.db.session import get_connection

logger = logging.getLogger("app.db")


def _sqlstate(exc: BaseException) -> str:
    original = getattr(exc, "orig", None)
    return str(
        getattr(original, "sqlstate", None)
        or getattr(original, "pgcode", None)
        or ""
    )


def _translate_error(exc: BaseException) -> None:
    code = _sqlstate(exc)
    if code == "23505":
        raise ConflictError("Data sudah ada (melanggar unique constraint)") from exc
    if code == "23503":
        raise BadRequestError("Referensi tidak valid (foreign key tidak ditemukan)") from exc
    if code in {"23502", "23514", "22P02", "22003"}:
        raise BadRequestError("Data tidak sesuai dengan batasan database") from exc
    logger.exception("Operasi PostgreSQL gagal", exc_info=exc)
    raise UpstreamError("Database gagal memproses permintaan") from exc


def fetch_all(sql: str, params: dict[str, Any] | None = None) -> list[dict]:
    try:
        with get_connection() as connection:
            rows = connection.execute(text(sql), params or {}).mappings().all()
            return [dict(row) for row in rows]
    except (IntegrityError, SQLAlchemyError) as exc:
        _translate_error(exc)


def fetch_one(sql: str, params: dict[str, Any] | None = None) -> dict | None:
    try:
        with get_connection() as connection:
            row = connection.execute(text(sql), params or {}).mappings().first()
            return dict(row) if row is not None else None
    except (IntegrityError, SQLAlchemyError) as exc:
        _translate_error(exc)


def fetch_all_with_count(
    select_sql: str,
    count_sql: str,
    params: dict[str, Any] | None = None,
) -> tuple[list[dict], int]:
    try:
        query_params = params or {}
        count_params = {key: value for key, value in query_params.items() if key not in {"limit", "offset"}}
        with get_connection() as connection:
            count = connection.execute(text(count_sql), count_params).scalar_one()
            rows = connection.execute(text(select_sql), query_params).mappings().all()
            return [dict(row) for row in rows], int(count or 0)
    except (IntegrityError, SQLAlchemyError) as exc:
        _translate_error(exc)


def execute_returning(sql: str, params: dict[str, Any] | None = None) -> dict | None:
    try:
        with get_connection(write=True) as connection:
            row = connection.execute(text(sql), params or {}).mappings().first()
            return dict(row) if row is not None else None
    except (IntegrityError, SQLAlchemyError) as exc:
        _translate_error(exc)


def execute_returning_all(sql: str, params: dict[str, Any] | None = None) -> list[dict]:
    """Sama seperti execute_returning, tetapi mengembalikan SEMUA baris.

    Dipakai operasi tulis yang perlu tahu berapa baris terpengaruh
    (mis. mencabut seluruh sesi milik satu user).
    """
    try:
        with get_connection(write=True) as connection:
            rows = connection.execute(text(sql), params or {}).mappings().all()
            return [dict(row) for row in rows]
    except (IntegrityError, SQLAlchemyError) as exc:
        _translate_error(exc)
