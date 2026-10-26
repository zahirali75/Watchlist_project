"""Peta endpoint modul watchlists.

Perhatikan: `user_id` tidak lagi dikirim di body. Pemilik data diambil dari
token JWT, jadi tidak mungkin menambah/mengubah watchlist user lain.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import get_current_user
from app.core.pagination import Pagination, pagination_params
from app.watchlists import service
from app.watchlists.schemas import WatchlistCreate, WatchlistUpdate, WatchStatus

router = APIRouter(prefix="/watchlists", tags=["Watchlist"])


@router.get("/me")
def get_my_watchlist(
    status: WatchStatus | None = Query(None, description="Filter status"),
    pagination: Pagination = Depends(pagination_params),
    current_user: dict = Depends(get_current_user),
):
    result = service.get_watchlist(
        user_id=current_user["user_id"],
        current_user_id=current_user["user_id"],
        status=status,
        pagination=pagination,
    )
    return {
        "success": True,
        "count": len(result["items"]),
        "total": result["total"],
        "page": pagination.page,
        "limit": pagination.limit,
        "data": result["items"],
    }


@router.get("/me/stats", tags=["Stats"])
def get_my_stats(current_user: dict = Depends(get_current_user)):
    stats = service.get_user_stats(current_user["user_id"])
    return {"success": True, **stats}


@router.get("/{user_id}")
def get_watchlist_by_user(
    user_id: str,
    status: WatchStatus | None = Query(None),
    pagination: Pagination = Depends(pagination_params),
    current_user: dict = Depends(get_current_user),
):
    """Dipertahankan untuk kompatibilitas frontend; tetap dijaga ownership."""
    result = service.get_watchlist(
        user_id=user_id,
        current_user_id=current_user["user_id"],
        status=status,
        pagination=pagination,
    )
    return {
        "success": True,
        "count": len(result["items"]),
        "total": result["total"],
        "page": pagination.page,
        "limit": pagination.limit,
        "data": result["items"],
    }


@router.post("", status_code=201)
def add_to_watchlist(payload: WatchlistCreate, current_user: dict = Depends(get_current_user)):
    item = service.add_to_watchlist(payload, current_user_id=current_user["user_id"])
    return {"success": True, "message": "Film berhasil ditambahkan ke watchlist", "data": item}


@router.put("/{watchlist_id}")
def update_watchlist_item(
    watchlist_id: int,
    payload: WatchlistUpdate,
    current_user: dict = Depends(get_current_user),
):
    item = service.update_watchlist_item(
        watchlist_id, payload, current_user_id=current_user["user_id"]
    )
    return {"success": True, "message": "Watchlist item berhasil diupdate", "data": item}


@router.delete("/{watchlist_id}")
def delete_watchlist_item(watchlist_id: int, current_user: dict = Depends(get_current_user)):
    item = service.delete_watchlist_item(watchlist_id, current_user_id=current_user["user_id"])
    return {"success": True, "message": "Watchlist item berhasil dihapus", "data": item}
