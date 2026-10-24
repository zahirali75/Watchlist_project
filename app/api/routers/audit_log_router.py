"""Endpoint audit log (khusus admin)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import require_admin
from app.core.pagination import Pagination, pagination_params
from app.services import audit_log_service

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"], dependencies=[Depends(require_admin)])


@router.get("")
def get_all_audit_logs(pagination: Pagination = Depends(pagination_params)):
    result = audit_log_service.get_all_audit_logs(pagination)
    return {
        "success": True,
        "count": len(result["items"]),
        "total": result["total"],
        "page": pagination.page,
        "limit": pagination.limit,
        "data": result["items"],
    }


@router.get("/{log_id}")
def get_audit_log_by_id(log_id: int):
    log = audit_log_service.find_audit_log_by_id(log_id)
    return {"success": True, "message": "Audit log berhasil diambil", "data": log}
