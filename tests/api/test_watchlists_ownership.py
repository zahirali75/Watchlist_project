"""Ownership watchlist: user A tidak boleh menyentuh item user B."""
from __future__ import annotations

from app.watchlists import repository as watchlist_repository
from tests.conftest import OTHER_USER_ID, USER_ID

MINE = {"id": 5, "user_id": USER_ID, "movie_id": 1, "status": "watching", "notes": "catatan"}
THEIRS = {**MINE, "user_id": OTHER_USER_ID}


def test_ubah_milik_sendiri_ok_dan_status_tervalidasi(client, user_auth, monkeypatch):
    captured = {}
    monkeypatch.setattr(watchlist_repository, "find_by_id", lambda i: MINE)
    monkeypatch.setattr(watchlist_repository, "update", lambda i, p: captured.update(p) or {**MINE, **p})
    r = client.put("/watchlists/5", json={"status": "watched"}, headers=user_auth)
    assert r.status_code == 200 and captured == {"status": "watched"}


def test_notes_null_menghapus_catatan(client, user_auth, monkeypatch):
    captured = {}
    monkeypatch.setattr(watchlist_repository, "find_by_id", lambda i: MINE)
    monkeypatch.setattr(watchlist_repository, "update", lambda i, p: captured.update(p) or {**MINE, **p})
    assert client.put("/watchlists/5", json={"notes": None}, headers=user_auth).status_code == 200
    assert captured == {"notes": None}


def test_status_null_dan_body_kosong_400(client, user_auth, monkeypatch):
    monkeypatch.setattr(watchlist_repository, "find_by_id", lambda i: MINE)
    assert client.put("/watchlists/5", json={"status": None}, headers=user_auth).status_code == 400
    assert client.put("/watchlists/5", json={}, headers=user_auth).status_code == 400


def test_hapus_milik_sendiri_ok(client, user_auth, monkeypatch):
    monkeypatch.setattr(watchlist_repository, "find_by_id", lambda i: MINE)
    monkeypatch.setattr(watchlist_repository, "delete", lambda i: MINE)
    assert client.delete("/watchlists/5", headers=user_auth).status_code == 200


def test_hapus_milik_orang_lain_403_dan_tidak_menghapus(client, user_auth, monkeypatch):
    called = []
    monkeypatch.setattr(watchlist_repository, "find_by_id", lambda i: THEIRS)
    monkeypatch.setattr(watchlist_repository, "delete", lambda i: called.append(i))
    assert client.delete("/watchlists/5", headers=user_auth).status_code == 403
    assert called == []


def test_item_tidak_ada_404(client, user_auth, monkeypatch):
    monkeypatch.setattr(watchlist_repository, "find_by_id", lambda i: None)
    assert client.delete("/watchlists/999", headers=user_auth).status_code == 404
    assert client.put("/watchlists/999", json={"status": "watched"}, headers=user_auth).status_code == 404


def test_lihat_watchlist_orang_lain_403_termasuk_admin(client, user_auth, admin_auth, monkeypatch):
    assert client.get(f"/watchlists/{OTHER_USER_ID}", headers=user_auth).status_code == 403
    # Kontrak saat ini: watchlist bersifat pribadi, admin pun tidak boleh (perilaku asli, tidak diubah).
    assert client.get(f"/watchlists/{OTHER_USER_ID}", headers=admin_auth).status_code == 403
    assert client.get(f"/watchlists/{OTHER_USER_ID}", headers=user_auth).json()["data"]["errorCode"] == "FORBIDDEN"
