"""Smoke test ke server yang sedang jalan (data asli Supabase).

Jalankan: ./.venv/Scripts/python.exe scripts/smoke_check.py
Server harus sudah hidup di http://127.0.0.1:8010
Script ini MENULIS data uji (1 user + 1 watchlist) lalu MEMBERSIHKAN watchlist-nya.
"""
from __future__ import annotations

import time

import httpx

BASE = "http://127.0.0.1:8010"


def show(label: str, response: httpx.Response) -> None:
    body = response.text
    if len(body) > 300:
        body = body[:300] + "..."
    print(f"[{response.status_code}] {label}\n    {body}\n")


def main() -> None:
    with httpx.Client(base_url=BASE, timeout=30) as c:
        show("GET /health", c.get("/health"))
        show("GET /movies?limit=1 (data asli)", c.get("/movies", params={"limit": 1}))
        show("POST /movies tanpa token", c.post("/movies", json={}))
        show("GET /users tanpa token (dulu terbuka)", c.get("/users"))

        email = f"refactor.{int(time.time())}@example.com"  # .test ditolak email-validator (TLD reserved)
        reg = c.post("/auth/register", json={"email": email, "password": "rahasia123", "name": "Refactor Test"})
        show("POST /auth/register", reg)
        if reg.status_code != 201:
            return
        token = reg.json()["accessToken"]
        headers = {"Authorization": f"Bearer {token}"}

        show("POST /movies pakai token role=user (harus 403)", c.post("/movies", json={}, headers=headers))

        added = c.post("/watchlists", json={"movie_id": 1, "status": "watching"}, headers=headers)
        show("POST /watchlists", added)
        show("POST /watchlists lagi (duplikat, harus 409)", c.post("/watchlists", json={"movie_id": 1}, headers=headers))
        show("GET /watchlists/me", c.get("/watchlists/me", headers=headers))
        show("GET /watchlists/me/stats", c.get("/watchlists/me/stats", headers=headers))

        if added.status_code == 201:
            item_id = added.json()["data"]["id"]
            show(f"PUT /watchlists/{item_id}", c.put(f"/watchlists/{item_id}", json={"status": "watched"}, headers=headers))
            show(f"DELETE /watchlists/{item_id} (bersih-bersih)", c.delete(f"/watchlists/{item_id}", headers=headers))

        print(f"CATATAN: akun uji {email} dibuat di Supabase, hapus manual kalau perlu.")


if __name__ == "__main__":
    main()
