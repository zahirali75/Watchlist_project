"""Test register & login."""
from __future__ import annotations

import jwt as pyjwt

from app.core.config import get_settings
from app.users import repository as user_repository

USER_ROW = {
    "id": "11111111-1111-1111-1111-111111111111",
    "email": "zahir@example.com",
    "name": "Zahir",
    "role": "user",
}


def test_register_email_duplikat_409(client, monkeypatch):
    monkeypatch.setattr(user_repository, "find_by_email", lambda email: USER_ROW)

    response = client.post("/auth/register", json={"email": "zahir@example.com", "password": "rahasia123"})

    assert response.status_code == 409
    assert response.json()["data"]["errorCode"] == "CONFLICT"


def test_register_password_pendek_422(client):
    response = client.post("/auth/register", json={"email": "a@b.com", "password": "123"})

    assert response.status_code == 422


def test_register_sukses_token_bisa_dibaca_dan_password_di_hash(client, monkeypatch):
    captured = {}

    def fake_create(payload):
        captured.update(payload)
        return USER_ROW

    monkeypatch.setattr(user_repository, "find_by_email", lambda email: None)
    monkeypatch.setattr(user_repository, "create", fake_create)
    monkeypatch.setattr("app.auth.service.audit_log_service.create_audit_log", lambda *a, **k: None)

    response = client.post("/auth/register", json={"email": "zahir@example.com", "password": "rahasia123"})

    assert response.status_code == 201
    body = response.json()
    assert "accessToken" in body

    # password tidak pernah disimpan apa adanya
    assert captured["password_hash"] != "rahasia123"
    assert captured["password_hash"].startswith("$")

    payload = pyjwt.decode(body["accessToken"], get_settings().SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == USER_ROW["id"] and payload["role"] == "user"


def test_login_salah_401_pesan_generik(client, monkeypatch):
    monkeypatch.setattr(user_repository, "find_auth_by_email", lambda email: None)

    response = client.post("/auth/login", json={"email": "zahir@example.com", "password": "apapun"})

    assert response.status_code == 401
    assert response.json()["message"] == "Email atau password salah"


def test_login_benar_mengembalikan_token(client, monkeypatch):
    from app.core.security import hash_password

    monkeypatch.setattr(
        user_repository,
        "find_auth_by_email",
        lambda email: {**USER_ROW, "password_hash": hash_password("rahasia123")},
    )

    response = client.post("/auth/login", json={"email": "zahir@example.com", "password": "rahasia123"})

    assert response.status_code == 200
    assert response.json()["role"] == "user"
