"""Pencatatan audit (dulu tidak ada sama sekali di CineList)."""
from __future__ import annotations

import logging

from app.core.exceptions import NotFoundError
from app.core.pagination import Pagination
from app.repositories import audit_log_repository as repo
from app.schemas.audit_log_schema import AuditLogCreate

logger = logging.getLogger("cinelist")


def create_audit_log(payload: AuditLogCreate, actor_id: str | None = None) -> dict | None:
    """Sengaja TIDAK melempar error kalau gagal: audit tidak boleh menggagalkan
    operasi utama (pola yang sama dipakai repo Pola Parking)."""
    try:
        return repo.create(payload.model_dump() | {"created_by": actor_id or payload.created_by})
    except Exception:
        logger.exception("Gagal menulis audit log (operasi utama tetap lanjut)")
        return None


def get_all_audit_logs(pagination: Pagination | None = None) -> dict:
    items, total = repo.find_all(pagination)
    return {"items": items, "total": total}


def find_audit_log_by_id(log_id: int) -> dict:
    log = repo.find_by_id(log_id)
    if not log:
        raise NotFoundError(f"Audit log {log_id} tidak ditemukan")
    return log
