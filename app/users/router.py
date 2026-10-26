"""Endpoint users. Seluruh modul dijaga admin (seperti user.route.ts di repo Pola)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth.dependencies import require_admin
from app.core.pagination import Pagination, pagination_params
from app.users import service
from app.watchlists import service as watchlist_service

router = APIRouter(prefix="/users", tags=["Users"], dependencies=[Depends(require_admin)])


@router.get("")
def get_all_users(pagination: Pagination = Depends(pagination_params)):
    result = service.get_all_users(pagination)
    return {
        "success": True,
        "count": len(result["items"]),
        "total": result["total"],
        "page": pagination.page,
        "limit": pagination.limit,
        "data": result["items"],
    }


@router.get("/{user_id}/stats", tags=["Stats"])
def get_user_stats_by_id(user_id: str):
    """Versi admin dari /watchlists/me/stats (dulu endpoint ini terbuka untuk umum)."""
    service.find_user_by_id(user_id)  # 404 bila user tidak ada (dulu: statistik 0)
    stats = watchlist_service.get_user_stats(user_id)
    return {"success": True, **stats}


@router.get("/{user_id}")
def get_user_by_id(user_id: str):
    user = service.find_user_by_id(user_id)
    return {"success": True, "message": "User berhasil diambil", "data": user}
