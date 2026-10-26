"""Perilaku hardening: rate limit per IP, validasi input, format error seragam.

Tes ini tanpa database (repository di-stub oleh conftest / monkeypatch).
"""
from __future__ import annotations


from app.auth import service as auth_service
from app.core.config import get_settings
from app.movies import repository as movie_repository
from app.users import repository as user_repository



def test_password_spraying_dari_satu_ip_diblokir(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "LOGIN_IP_MAX_ATTEMPTS", 3)
    monkeypatch.setattr(get_settings(), "LOGIN_MAX_ATTEMPTS", 100)  # isolasi: hanya uji batas IP
    monkeypatch.setattr(auth_service.user_service, "find_auth_by_email", lambda email: None)
    codes = [
        client.post("/auth/login", json={"email": f"orang{i}@example.com", "password": "salahsalah"}).status_code
        for i in range(5)
    ]
    assert codes[:3] == [401, 401, 401] and codes[3:] == [429, 429]


def test_poster_url_javascript_ditolak(admin_auth, client):
    body = {"title": "X", "release_year": 2000, "genre": "Drama", "poster_url": "javascript:alert(1)"}
    response = client.post("/movies", json=body, headers=admin_auth)
    assert response.status_code == 422
    assert response.json()["data"]["errorCode"] == "VALIDATION_ERROR"


def test_poster_url_data_uri_ditolak_dan_https_diterima(admin_auth, client, monkeypatch):
    bad = {"title": "X", "release_year": 2000, "genre": "Drama", "poster_url": "data:text/html;base64,AAAA"}
    assert client.post("/movies", json=bad, headers=admin_auth).status_code == 422
    monkeypatch.setattr(movie_repository, "create", lambda payload: {"id": 1, **payload})
    good = {"title": "X", "release_year": 2000, "genre": "Drama", "poster_url": "https://image.tmdb.org/t/p/w500/a.jpg"}
    assert client.post("/movies", json=good, headers=admin_auth).status_code == 201


def test_overview_dan_notes_terlalu_panjang_ditolak(admin_auth, client, user_auth):
    long_text = "a" * 10_001
    movie = {"title": "X", "release_year": 2000, "genre": "Drama", "overview": long_text}
    assert client.post("/movies", json=movie, headers=admin_auth).status_code == 422
    note = {"movie_id": 1, "notes": "a" * 2001}
    assert client.post("/watchlists", json=note, headers=user_auth).status_code == 422


def test_rute_tidak_ada_memakai_format_error_seragam(client):
    response = client.get("/tidak-ada-rute")
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False and body["data"]["errorCode"] == "NOT_FOUND" and "detail" not in body


def test_metode_salah_memakai_format_error_seragam(client):
    response = client.delete("/health")
    assert response.status_code == 405
    body = response.json()
    assert body["data"]["errorCode"] == "METHOD_NOT_ALLOWED" and "detail" not in body


def test_user_id_bukan_uuid_menjadi_404_bukan_400_db(client, admin_auth, monkeypatch):
    called = {"db": False}

    def _fake(uid):
        called["db"] = True
        return None

    monkeypatch.setattr(user_repository, "find_by_id", _fake)
    response = client.get("/users/bukan-uuid", headers=admin_auth)
    assert response.status_code == 404
    assert response.json()["data"]["errorCode"] == "NOT_FOUND"
    assert called["db"] is False  # tidak pernah menyentuh database


def test_root_di_production_tidak_redirect_ke_docs_yang_mati(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "APP_ENV", "production")
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 200 and response.json()["success"] is True
    health = client.get("/health").json()
    assert health["data"]["docs"] is None


def test_page_terlalu_besar_ditolak_422_bukan_error_database(client):
    # Sebelumnya page=2^63 lolos ke database dan menghasilkan pesan error tipe data.
    response = client.get("/movies", params={"page": 2**63})
    assert response.status_code == 422
    assert response.json()["data"]["errorCode"] == "VALIDATION_ERROR"
