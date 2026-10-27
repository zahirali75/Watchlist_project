"""Endpoint profil milik sendiri (/users/me).

Dipisah dari app/users/router.py karena router itu dijaga admin SECARA
KESELURUHAN (dependencies=[Depends(require_admin)]). Kalau /users/me disisipkan
di sana, endpoint itu ikut tertutup untuk pengguna biasa.

Perhatikan urutan pendaftaran di app/main.py: profil_router didaftarkan DULUAN
sebelum users_router, supaya /users/me tidak tertangkap pola /users/{user_id}.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.users import service
from app.users.schemas import ProfileUpdate
from app.watchlists import service as watchlist_service

router = APIRouter(prefix="/users/me", tags=["Users"])


@router.get("")
def get_my_profile(current_user: dict = Depends(get_current_user)):
    """PENAMBAHAN BARU: pengguna biasa bisa melihat profilnya sendiri.

    Sebelumnya tidak ada jalur ini - satu-satunya cara melihat data user adalah
    endpoint admin, sehingga pengguna biasa selalu mendapat 403.
    """
    user = service.get_own_profile(current_user["user_id"])
    return {"success": True, "message": "Profil berhasil diambil", "data": user}


@router.put("")
def update_my_profile(payload: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    """PENAMBAHAN BARU: ubah nama tampilan sendiri (email & role tidak bisa)."""
    user = service.update_own_profile(current_user["user_id"], payload.name)
    return {"success": True, "message": "Profil berhasil diupdate", "data": user}


@router.get("/stats", tags=["Stats"])
def get_my_stats(current_user: dict = Depends(get_current_user)):
    """Ringkasan watchlist milik sendiri (bentuknya sama dengan /watchlists/me/stats)."""
    stats = watchlist_service.get_user_stats(current_user["user_id"])
    return {"success": True, **stats}
