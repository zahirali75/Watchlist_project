"""Login, token, dan RBAC: sisi gagal yang penting."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt as pyjwt
import pytest

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.users import repository as user_repository
from tests.conftest import ADMIN_ID, USER_ID

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


@pytest.fixture(scope="module")
def stored_hash() -> str:
    return hash_password("rahasia123")  # sekali saja: PBKDF2 600k rounds sengaja lambat


def _login_user(monkeypatch, stored_hash):
    monkeypatch.setattr(
        user_repository,
        "find_auth_by_email",
        lambda email: {"id": USER_ID, "email": email, "name": "Z", "role": "user", "password_hash": stored_hash},
    )


def test_login_sukses_mengembalikan_token_tanpa_hash(client, monkeypatch, stored_hash):
    _login_user(monkeypatch, stored_hash)
    r = client.post("/auth/login", json={"email": "z@x.com", "password": "rahasia123"})
    assert r.status_code == 200
    body = r.json()
    assert body["accessToken"] and "password" not in str(body).lower()


def test_login_password_salah_dan_email_tak_dikenal_pesannya_sama(client, monkeypatch, stored_hash):
    _login_user(monkeypatch, stored_hash)
    salah = client.post("/auth/login", json={"email": "z@x.com", "password": "salahsalah"})
    monkeypatch.setattr(user_repository, "find_auth_by_email", lambda email: None)
    tak_dikenal = client.post("/auth/login", json={"email": "x@x.com", "password": "salahsalah"})
    assert salah.status_code == tak_dikenal.status_code == 401
    assert salah.json() == tak_dikenal.json()


def test_login_diblokir_429_setelah_gagal_berulang(client, monkeypatch):
    monkeypatch.setattr(user_repository, "find_auth_by_email", lambda email: None)
    limit = get_settings().LOGIN_MAX_ATTEMPTS
    for _ in range(limit):
        assert client.post("/auth/login", json={"email": "a@x.com", "password": "salahsalah"}).status_code == 401
    r = client.post("/auth/login", json={"email": "a@x.com", "password": "salahsalah"})
    assert r.status_code == 429 and r.json()["data"]["errorCode"] == "TOO_MANY_REQUESTS"


def test_token_kedaluwarsa_401(client):
    settings = get_settings()
    token = pyjwt.encode(
        {"sub": USER_ID, "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}, settings.SECRET_KEY, algorithm="HS256"
    )
    r = client.get("/watchlists/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401 and "kedaluwarsa" in r.json()["message"]


def test_token_sampah_atau_secret_salah_401(client):
    assert client.get("/watchlists/me", headers={"Authorization": "Bearer abc"}).status_code == 401
    forged = pyjwt.encode({"sub": USER_ID, "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}, "x" * 40, algorithm="HS256")
    assert client.get("/watchlists/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_token_sub_bukan_uuid_401(client):
    token = create_access_token("bukan-uuid", "admin")
    assert client.get("/users", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_token_user_yang_sudah_dihapus_401(client):
    token = create_access_token("99999999-9999-9999-9999-999999999999", "admin")  # tidak ada di "database"
    assert client.get("/users", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_role_dicabut_token_admin_lama_menjadi_403(client, monkeypatch):
    token = create_access_token(ADMIN_ID, "admin")  # token masih berisi role admin
    monkeypatch.setattr(user_repository, "find_identity", lambda uid: {"id": uid, "role": "user"})  # role sudah dicabut
    r = client.get("/users", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_audit_logs_user_biasa_403_admin_ok(client, user_auth, admin_auth, monkeypatch):
    from app.audit_logs import repository as audit_repo

    monkeypatch.setattr(audit_repo, "find_all", lambda pagination=None: ([], 0))
    assert client.get("/audit-logs", headers=user_auth).status_code == 403
    assert client.get("/audit-logs", headers=admin_auth).status_code == 200
    assert client.get("/audit-logs").status_code == 401
