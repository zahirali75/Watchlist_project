"""Test modul users: dulu endpoint /users terbuka, sekarang admin-only."""
from __future__ import annotations

from app.users import repository as user_repository

ADMIN_ID = "22222222-2222-2222-2222-222222222222"
USER_ROW = {"id": "11111111-1111-1111-1111-111111111111", "name": "Zahir", "email": "a@b.com", "role": "user"}


def test_users_tanpa_token_401(client):
    assert client.get("/users").status_code == 401


def test_users_token_user_biasa_403(client, user_auth):
    assert client.get("/users", headers=user_auth).status_code == 403


def test_users_admin_ok_dan_password_tidak_muncul(client, admin_auth, monkeypatch):
    monkeypatch.setattr(user_repository, "find_all", lambda pagination=None: ([USER_ROW], 1))

    response = client.get("/users", headers=admin_auth)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert "password_hash" not in str(body)
