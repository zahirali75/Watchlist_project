"""Test watchlist: ownership, validasi status, dan stats."""
from __future__ import annotations

from app.repositories import watchlist_repository

OWNER_ID = "11111111-1111-1111-1111-111111111111"
ITEM = {"id": 5, "user_id": OWNER_ID, "movie_id": 1, "status": "watching", "notes": None}


def test_watchlist_me_tanpa_token_401(client):
    assert client.get("/watchlists/me").status_code == 401


def test_watchlist_me_publik_ok(client, user_auth, monkeypatch):
    monkeypatch.setattr(watchlist_repository, "find_all_by_user", lambda *a, **k: ([ITEM], 1))

    response = client.get("/watchlists/me", headers=user_auth)

    assert response.status_code == 200
    assert response.json()["data"][0]["movie_id"] == 1


def test_akses_watchlist_user_lain_403(client, user_auth):
    response = client.get("/watchlists/99999999-9999-9999-9999-999999999999", headers=user_auth)

    assert response.status_code == 403
    assert response.json()["data"]["errorCode"] == "FORBIDDEN"


def test_status_tidak_valid_422(client, user_auth):
    response = client.post(
        "/watchlists", json={"movie_id": 1, "status": "nonton_bareng"}, headers=user_auth
    )
    assert response.status_code == 422


def test_tambah_duplikat_409(client, user_auth, monkeypatch):
    monkeypatch.setattr("app.services.watchlist_service.movie_repository.find_by_id", lambda i: {"id": i})
    monkeypatch.setattr(watchlist_repository, "find_by_user_and_movie", lambda u, m: ITEM)

    response = client.post("/watchlists", json={"movie_id": 1}, headers=user_auth)

    assert response.status_code == 409
    assert response.json()["data"]["errorCode"] == "CONFLICT"


def test_tambah_film_tidak_ada_404(client, user_auth, monkeypatch):
    monkeypatch.setattr("app.services.watchlist_service.movie_repository.find_by_id", lambda i: None)

    response = client.post("/watchlists", json={"movie_id": 123456}, headers=user_auth)

    assert response.status_code == 404


def test_update_milik_orang_lain_403(client, user_auth, monkeypatch):
    monkeypatch.setattr(
        watchlist_repository, "find_by_id", lambda i: {**ITEM, "user_id": "99999999-9999-9999-9999-999999999999"}
    )

    response = client.put("/watchlists/5", json={"status": "watched"}, headers=user_auth)

    assert response.status_code == 403


def test_stats_pakai_count_database_ok(client, user_auth, monkeypatch):
    calls = {}

    # total dipanggil dengan status=None, sisanya per status
    counts = {None: 7, "watched": 3, "watching": 2, "want_to_watch": 2}

    def fake_count(user_id, status=None):
        calls[status] = counts[status]
        return calls[status]

    monkeypatch.setattr(watchlist_repository, "count_by_status", fake_count)

    response = client.get("/watchlists/me/stats", headers=user_auth)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 7 and body["watched"] == 3 and body["wantToWatch"] == 2
