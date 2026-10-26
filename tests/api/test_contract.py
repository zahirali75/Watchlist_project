"""Kontrak API: daftar endpoint tidak berubah diam-diam; OpenAPI valid."""
from __future__ import annotations

from app.main import app
from app.users import repository as user_repository

# Snapshot endpoint (method, path, butuh login). Ubah HANYA bila perubahan memang disengaja,
# lalu perbarui docs/api.md.
EXPECTED = {
    ("GET", "/health", False),
    ("GET", "/health/db", False),
    ("POST", "/auth/register", False),
    ("POST", "/auth/login", False),
    ("GET", "/movies", False),
    ("POST", "/movies", True),
    ("GET", "/movies/{movie_id}", False),
    ("PUT", "/movies/{movie_id}", True),
    ("DELETE", "/movies/{movie_id}", True),
    ("GET", "/watchlists/me", True),
    ("GET", "/watchlists/me/stats", True),
    ("GET", "/watchlists/{user_id}", True),
    ("POST", "/watchlists", True),
    ("PUT", "/watchlists/{watchlist_id}", True),
    ("DELETE", "/watchlists/{watchlist_id}", True),
    ("GET", "/users", True),
    ("GET", "/users/{user_id}", True),
    ("GET", "/users/{user_id}/stats", True),
    ("GET", "/audit-logs", True),
    ("GET", "/audit-logs/{log_id}", True),
}


def test_openapi_terbangun_dan_daftar_endpoint_sesuai_snapshot():
    spec = app.openapi()
    actual = {(m.upper(), path, bool(op.get("security"))) for path, ops in spec["paths"].items() for m, op in ops.items()}
    assert actual == EXPECTED


def test_endpoint_terproteksi_menolak_tanpa_token(client):
    for method, path, needs_auth in EXPECTED:
        if needs_auth:
            url = path.replace("{movie_id}", "1").replace("{watchlist_id}", "1").replace("{log_id}", "1").replace(
                "{user_id}", "11111111-1111-1111-1111-111111111111"
            )
            assert client.request(method, url).status_code == 401, (method, path)


def test_format_error_seragam(client):
    body = client.get("/watchlists/me").json()
    assert body["success"] is False and "message" in body and "errorCode" in body["data"]
    validation = client.post("/auth/register", json={"email": "bukan-email", "password": "1"}).json()
    assert validation["data"]["errorCode"] == "VALIDATION_ERROR" and isinstance(validation["data"]["errorMeta"], list)


def test_response_user_tidak_pernah_memuat_password_hash(client, admin_auth, monkeypatch):
    row = {"id": "11111111-1111-1111-1111-111111111111", "name": "Z", "email": "z@x.com", "role": "user", "created_at": "2026-01-01T00:00:00"}
    monkeypatch.setattr(user_repository, "find_all", lambda pagination=None: ([row], 1))
    monkeypatch.setattr(user_repository, "find_by_id", lambda uid: row)
    for url in ("/users", "/users/11111111-1111-1111-1111-111111111111"):
        assert "password" not in client.get(url, headers=admin_auth).text.lower()


def test_stats_user_tidak_ada_404(client, admin_auth, monkeypatch):
    monkeypatch.setattr(user_repository, "find_by_id", lambda uid: None)
    assert client.get("/users/44444444-4444-4444-4444-444444444444/stats", headers=admin_auth).status_code == 404


def test_cors_hanya_origin_terdaftar(client):
    ok = client.options("/movies", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    bad = client.options("/movies", headers={"Origin": "http://jahat.example", "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in bad.headers
