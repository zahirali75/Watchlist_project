"""Endpoint profil sendiri, sesi (refresh/logout), dan password.

Tes di folder ini TIDAK menyentuh database: repository di-stub oleh konftes.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.auth import repository as token_repository
from app.core.security import hash_password, hash_token
from app.users import repository as user_repository
from tests.conftest import USER_ID

USER_ROW = {
    "id": USER_ID,
    "email": "zahir@example.com",
    "name": "Zahir",
    "role": "user",
    "created_at": "2026-01-01T00:00:00",
}


# ---------------------------------------------------------------------------
# /users/me - dulu pengguna biasa TIDAK punya jalur melihat profilnya sendiri
# ---------------------------------------------------------------------------
def test_profil_sendiri_bisa_dilihat_pengguna_biasa(client, user_auth, monkeypatch):
    monkeypatch.setattr(user_repository, "find_by_id", lambda uid: USER_ROW)

    response = client.get("/users/me", headers=user_auth)

    assert response.status_code == 200
    assert response.json()["data"]["email"] == "zahir@example.com"


def test_profil_sendiri_tanpa_token_401(client):
    assert client.get("/users/me").status_code == 401


def test_ubah_nama_sendiri(client, user_auth, monkeypatch):
    captured = {}

    def fake_update(user_id, name):
        captured["user_id"] = user_id
        captured["name"] = name
        return {**USER_ROW, "name": name}

    monkeypatch.setattr(user_repository, "update_profile", fake_update)

    response = client.put("/users/me", headers=user_auth, json={"name": "Zahir Baru"})

    assert response.status_code == 200
    assert captured == {"user_id": USER_ID, "name": "Zahir Baru"}
    assert response.json()["data"]["name"] == "Zahir Baru"


def test_profil_sendiri_tidak_pernah_memuat_password(client, user_auth, monkeypatch):
    monkeypatch.setattr(user_repository, "find_by_id", lambda uid: USER_ROW)
    assert "password" not in client.get("/users/me", headers=user_auth).text.lower()


def test_statistik_sendiri_sesuai_token_dbukan_id_dari_url(client, user_auth, monkeypatch):
    # Endpoint ini harus memakai identitas dari token, bukan parameter yang bisa dipalsukan.
    called = {}

    def fake_stats(user_id):
        called["user_id"] = user_id
        return {"total": 0, "watched": 0, "watching": 0, "wantToWatch": 0}

    monkeypatch.setattr("app.watchlists.service.get_user_stats", fake_stats)

    response = client.get("/users/me/stats", headers=user_auth)

    assert response.status_code == 200
    assert called["user_id"] == USER_ID


# ---------------------------------------------------------------------------
# /auth/refresh - perpanjangan sesi
# ---------------------------------------------------------------------------
def _stored_token(**overrides) -> dict:
    base = {
        "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "user_id": USER_ID,
        "expires_at": datetime.now(timezone.utc) + timedelta(days=1),
        "revoked_at": None,
    }
    return {**base, **overrides}


def test_refresh_token_kedaluwarsa_ditolak(client, monkeypatch):
    monkeypatch.setattr(
        token_repository,
        "find_refresh_token",
        lambda token_hash: _stored_token(expires_at=datetime.now(timezone.utc) - timedelta(minutes=1)),
    )

    response = client.post("/auth/refresh", json={"refreshToken": "x" * 32})

    assert response.status_code == 401
    assert response.json()["data"]["errorCode"] == "UNAUTHORIZED"


def test_refresh_token_sudah_dicabut_ditolak(client, monkeypatch):
    # Bukti rotasi: token yang sudah dipakai (dicabut) tidak bisa dipakai dua kali.
    monkeypatch.setattr(
        token_repository,
        "find_refresh_token",
        lambda token_hash: _stored_token(revoked_at=datetime.now(timezone.utc)),
    )

    assert client.post("/auth/refresh", json={"refreshToken": "x" * 32}).status_code == 401


def test_refresh_token_asing_ditolak(client, monkeypatch):
    monkeypatch.setattr(token_repository, "find_refresh_token", lambda token_hash: None)

    assert client.post("/auth/refresh", json={"refreshToken": "x" * 32}).status_code == 401


def test_refresh_token_benar_mengembalikan_access_token_dan_merotasi_token(client, monkeypatch):
    revoked = []
    monkeypatch.setattr(token_repository, "find_refresh_token", lambda token_hash: _stored_token())
    monkeypatch.setattr(token_repository, "revoke_refresh_token", lambda token_id: revoked.append(token_id) or True)
    monkeypatch.setattr(token_repository, "create_refresh_token", lambda payload: {"id": "b" * 8, **payload})

    response = client.post("/auth/refresh", json={"refreshToken": "x" * 32})

    assert response.status_code == 200
    body = response.json()
    assert body["accessToken"] and body["refreshToken"]
    # Token lama harus langsung dicabut (rotasi), bukan dibiarkan hidup.
    assert revoked == ["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"]


def test_refresh_token_dicari_berdasarkan_hash_bukan_teks_asli(client, monkeypatch):
    seen = {}
    monkeypatch.setattr(token_repository, "find_refresh_token", lambda token_hash: seen.setdefault("hash", token_hash) and None)
    monkeypatch.setattr(token_repository, "create_refresh_token", lambda payload: {})

    client.post("/auth/refresh", json={"refreshToken": "token-asli-jangan-disimpan"})

    assert seen["hash"] == hash_token("token-asli-jangan-disimpan")
    assert seen["hash"] != "token-asli-jangan-disimpan"


# ---------------------------------------------------------------------------
# /auth/logout
# ---------------------------------------------------------------------------
def test_logout_mencabut_sesi_milik_sendiri(client, user_auth, monkeypatch):
    revoked = []
    monkeypatch.setattr(token_repository, "find_refresh_token", lambda token_hash: _stored_token())
    monkeypatch.setattr(token_repository, "revoke_refresh_token", lambda token_id: revoked.append(token_id) or True)

    response = client.post("/auth/logout", headers=user_auth, json={"refreshToken": "x" * 32})

    assert response.status_code == 200
    assert revoked == ["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"]


def test_logout_tidak_bisa_mencabut_sesi_orang_lain(client, user_auth, monkeypatch):
    revoked = []
    monkeypatch.setattr(
        token_repository,
        "find_refresh_token",
        lambda token_hash: _stored_token(user_id="99999999-9999-9999-9999-999999999999"),
    )
    monkeypatch.setattr(token_repository, "revoke_refresh_token", lambda token_id: revoked.append(token_id) or True)

    response = client.post("/auth/logout", headers=user_auth, json={"refreshToken": "x" * 32})

    assert response.status_code == 200  # idempoten
    assert revoked == []


def test_logout_tanpa_token_401(client):
    assert client.post("/auth/logout", json={"refreshToken": "x" * 32}).status_code == 401


# ---------------------------------------------------------------------------
# /auth/change-password
# ---------------------------------------------------------------------------
def test_ganti_password_wajib_password_lama_yang_benar(client, user_auth, monkeypatch):
    monkeypatch.setattr(
        user_repository,
        "find_auth_by_id",
        lambda uid: {**USER_ROW, "password_hash": hash_password("lama12345")},
    )

    response = client.post(
        "/auth/change-password",
        headers=user_auth,
        json={"currentPassword": "salah12345", "newPassword": "baru123456"},
    )

    assert response.status_code == 401


def test_ganti_password_sukses_dan_mencabut_semua_sesi(client, user_auth, monkeypatch):
    updated = {}
    revoked = []
    monkeypatch.setattr(
        user_repository,
        "find_auth_by_id",
        lambda uid: {**USER_ROW, "password_hash": hash_password("lama12345")},
    )
    monkeypatch.setattr(
        user_repository,
        "update_password_hash",
        lambda uid, hashed: updated.update({"user_id": uid, "hash": hashed}) or True,
    )
    monkeypatch.setattr(token_repository, "revoke_all_refresh_tokens", lambda uid: revoked.append(uid) or 3)
    monkeypatch.setattr("app.auth.service.audit_log_service.create_audit_log", lambda *a, **k: None)

    response = client.post(
        "/auth/change-password",
        headers=user_auth,
        json={"currentPassword": "lama12345", "newPassword": "baru123456"},
    )

    assert response.status_code == 200
    assert updated["hash"] != hash_password("lama12345") and updated["hash"].startswith("$")
    # Bila password berubah karena akun disalahgunakan, sesi penyerang harus mati.
    assert revoked == [USER_ID]
    assert response.json()["sessionsRevoked"] == 3


def test_ganti_password_baru_terlalu_pendek_422(client, user_auth):
    response = client.post(
        "/auth/change-password",
        headers=user_auth,
        json={"currentPassword": "lama12345", "newPassword": "pendek"},
    )

    assert response.status_code == 422


def test_ganti_password_sama_dengan_lama_ditolak(client, user_auth, monkeypatch):
    monkeypatch.setattr(
        user_repository,
        "find_auth_by_id",
        lambda uid: {**USER_ROW, "password_hash": hash_password("lama12345")},
    )

    response = client.post(
        "/auth/change-password",
        headers=user_auth,
        json={"currentPassword": "lama12345", "newPassword": "lama12345"},
    )

    assert response.status_code == 400


# ---------------------------------------------------------------------------
# /auth/forgot-password & /auth/reset-password
# ---------------------------------------------------------------------------
def test_lupa_password_email_tak_terdaftar_tetap_jawab_sama(client, monkeypatch):
    # Anti penebakan akun: balasannya tidak boleh membedakan email terdaftar atau bukan.
    monkeypatch.setattr(user_repository, "find_auth_by_email", lambda email: None)

    response = client.post("/auth/forgot-password", json={"email": "tidak-ada@example.com"})

    assert response.status_code == 200
    assert response.json()["emailSent"] is False
    assert "terdaftar" in response.json()["message"]


def test_lupa_password_mengirim_tautan_dan_menyimpan_hanya_hash(client, monkeypatch):
    stored = {}
    monkeypatch.setattr(
        user_repository,
        "find_auth_by_email",
        lambda email: {"id": USER_ID, "email": "zahir@example.com"},
    )
    monkeypatch.setattr(token_repository, "create_password_reset", lambda payload: stored.update(payload) or {"id": "x"})
    monkeypatch.setattr(
        "app.auth.service.notification_service.send_password_reset_email",
        lambda email, token: bool(stored.setdefault("raw_token", token)),
    )

    response = client.post("/auth/forgot-password", json={"email": "zahir@example.com"})

    assert response.status_code == 200
    assert response.json()["emailSent"] is True
    assert stored["token_hash"] == hash_token(stored["raw_token"])
    assert stored["user_id"] == USER_ID


def test_reset_password_token_asing_ditolak(client, monkeypatch):
    monkeypatch.setattr(token_repository, "find_password_reset", lambda token_hash: None)

    response = client.post("/auth/reset-password", json={"token": "x" * 32, "newPassword": "baru123456"})

    assert response.status_code == 400


def test_reset_password_token_kedaluwarsa_ditolak(client, monkeypatch):
    monkeypatch.setattr(
        token_repository,
        "find_password_reset",
        lambda token_hash: {
            "id": "r1",
            "user_id": USER_ID,
            "expires_at": datetime.now(timezone.utc) - timedelta(minutes=1),
            "used_at": None,
        },
    )

    assert client.post("/auth/reset-password", json={"token": "x" * 32, "newPassword": "baru123456"}).status_code == 400


def test_reset_password_token_sudah_dipakai_ditolak(client, monkeypatch):
    # Token sekali pakai: setelah dipakai, tidak bisa dipakai lagi.
    monkeypatch.setattr(
        token_repository,
        "find_password_reset",
        lambda token_hash: {
            "id": "r1",
            "user_id": USER_ID,
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
            "used_at": datetime.now(timezone.utc),
        },
    )

    assert client.post("/auth/reset-password", json={"token": "x" * 32, "newPassword": "baru123456"}).status_code == 400


def test_reset_password_sukses_menandai_terpakai_dan_mencabut_sesi(client, monkeypatch):
    marked = []
    revoked = []
    monkeypatch.setattr(
        token_repository,
        "find_password_reset",
        lambda token_hash: {
            "id": "r1",
            "user_id": USER_ID,
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
            "used_at": None,
        },
    )
    monkeypatch.setattr(
        user_repository,
        "update_password_hash",
        lambda uid, hashed: hashed.startswith("$") and uid == USER_ID,
    )
    monkeypatch.setattr(token_repository, "mark_password_reset_used", lambda reset_id: marked.append(reset_id) or True)
    monkeypatch.setattr(token_repository, "revoke_all_refresh_tokens", lambda uid: revoked.append(uid) or 1)
    monkeypatch.setattr("app.auth.service.audit_log_service.create_audit_log", lambda *a, **k: None)

    response = client.post("/auth/reset-password", json={"token": "x" * 32, "newPassword": "baru123456"})

    assert response.status_code == 200
    assert marked == ["r1"] and revoked == [USER_ID]


def test_token_pendek_422(client):
    assert client.post("/auth/reset-password", json={"token": "pendek", "newPassword": "baru123456"}).status_code == 422
